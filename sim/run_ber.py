"""BER/BLER vs SNR curves for the locked numerology.

Usage:
    python -m sim.run_ber                       # default sweep, AWGN + impaired
    python -m sim.run_ber --mcs 0 3 5 --frames 40
    python -m sim.run_ber --channel impaired    # CFO+multipath+PN+12-bit ADC

Results (PNG + CSV) land in sim/results/.
"""
from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

import numpy as np

from . import channel
from .modem import Receiver, Transmitter
from .params import MCS_TABLE, NUM, phy_rate

RESULTS = Path(__file__).parent / "results"


def run_point(tx: Transmitter, rx: Receiver, mcs_idx: int, cfg_base: dict,
              snr_db: float, n_frames: int, payload_len: int, seed0: int):
    n_bit_err = n_bits = n_frame_err = 0
    rng = np.random.default_rng(1234)
    for f in range(n_frames):
        payload = rng.integers(0, 256, payload_len, dtype=np.uint8).tobytes()
        wave = tx.build_frame(payload, mcs_idx, rng=rng)
        cfg = channel.ChannelConfig(snr_db=snr_db, seed=seed0 + f, **cfg_base)
        out, dbg = rx.receive(channel.apply(wave, NUM, cfg))
        n_bits += 8 * payload_len
        if out is None or out != payload:
            n_frame_err += 1
            if out is not None and len(out) == len(payload):
                a = np.unpackbits(np.frombuffer(payload, np.uint8))
                b = np.unpackbits(np.frombuffer(out, np.uint8))
                n_bit_err += int(np.sum(a != b))
            else:
                n_bit_err += 4 * payload_len  # count lost frame as 50% BER
    return n_bit_err / n_bits, n_frame_err / n_frames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mcs", type=int, nargs="+", default=[0, 2, 3, 5])
    ap.add_argument("--frames", type=int, default=30)
    ap.add_argument("--payload", type=int, default=300, help="bytes per frame")
    ap.add_argument("--channel", choices=["awgn", "impaired", "both"],
                    default="both")
    args = ap.parse_args()

    RESULTS.mkdir(exist_ok=True)
    tx, rx = Transmitter(NUM), Receiver(NUM)

    channels = {
        "awgn": dict(),
        # phase noise: 1 Hz Lorentzian linewidth is still >> the LMX2582's
        # integrated PN (~50 fs); 50 Hz is a stress value that breaks 64-QAM
        # (16 deg intra-symbol wander over the 256 us symbol).
        "impaired": dict(cfo_hz=870.0, rms_delay_spread_s=1e-6,
                         phase_noise_linewidth_hz=1.0, quantize_bits=12),
    }
    if args.channel != "both":
        channels = {args.channel: channels[args.channel]}

    all_rows = []
    curves = {}
    for ch_name, cfg_base in channels.items():
        for m in args.mcs:
            mcs = MCS_TABLE[m]
            ref = mcs.snr_ref_db + (2.0 if ch_name == "impaired" else 0.0)
            snrs = np.arange(ref - 6, ref + 5, 1.0)
            bers, blers = [], []
            t0 = time.time()
            for s in snrs:
                ber, bler = run_point(tx, rx, m, cfg_base, s, args.frames,
                                      args.payload,
                                      seed0=(int(s * 977) % 100003) + m * 13)
                bers.append(ber)
                blers.append(bler)
                all_rows.append((ch_name, m, mcs.name, s, ber, bler))
            curves[(ch_name, m)] = (snrs, bers, blers)
            print(f"[{ch_name}] MCS{m} {mcs.name} "
                  f"({phy_rate(NUM, mcs)/1e3:.0f} kbps): "
                  f"BLER {['%.2f' % b for b in blers]} @ "
                  f"SNR {snrs[0]:.0f}..{snrs[-1]:.0f} dB "
                  f"({time.time()-t0:.0f}s)")

    with open(RESULTS / "ber_results.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["channel", "mcs", "name", "snr_db", "ber", "bler"])
        w.writerows(all_rows)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    for metric, idx, fname in (("BER", 1, "ber_vs_snr.png"),
                               ("BLER", 2, "bler_vs_snr.png")):
        fig, axes = plt.subplots(1, len(channels), figsize=(6 * len(channels), 4.5),
                                 squeeze=False, sharey=True)
        for ax, ch_name in zip(axes[0], channels):
            for m in args.mcs:
                snrs, bers, blers = curves[(ch_name, m)]
                vals = (None, bers, blers)[idx]
                ax.semilogy(snrs, np.maximum(vals, 1e-6), marker="o",
                            label=f"MCS{m} {MCS_TABLE[m].name}")
            ax.set_title(f"{ch_name} — N=128, CP=16us, 52 data carriers")
            ax.set_xlabel("SNR in occupied BW [dB]")
            ax.grid(True, which="both", alpha=0.3)
            ax.legend(fontsize=8)
        axes[0][0].set_ylabel(metric)
        fig.tight_layout()
        fig.savefig(RESULTS / fname, dpi=130)
        print(f"wrote {RESULTS / fname}")


if __name__ == "__main__":
    main()
