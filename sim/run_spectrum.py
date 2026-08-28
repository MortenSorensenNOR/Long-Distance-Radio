"""TX spectrum vs the EN 300 220-2 V3.3.1 band-edge mask (Table 9).

Checks the golden-model TX output against the mask points derived in
docs/regulatory_notes.md section 2.1, for several shaping configs and for the
56- and 60-occupied-carrier variants.

Usage: python -m sim.run_spectrum      (writes sim/results/tx_spectrum.png)

Mask (1 kHz RBW, absolute, at 27 dBm mean ERP): 0 dBm at the band edge
(869.400 / 869.650), linear 180 dB/MHz down to -36 dBm at edge+200 kHz.
In-band mean PSD = 27 dBm - 10*log10(occupied_bw / 1 kHz).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal as sig

from .modem import Transmitter
from .params import NUM, Numerology

RESULTS = Path(__file__).parent / "results"
TX_POWER_DBM = 27.0
RBW = 1e3  # mask reference bandwidth


def tx_psd(tx: Transmitter, num: Numerology, n_frames: int = 8,
           payload_len: int = 1000, mcs: int = 5):
    rng = np.random.default_rng(7)
    frames = [tx.build_frame(rng.integers(0, 256, payload_len,
                                          dtype=np.uint8).tobytes(),
                             mcs, rng=rng) for _ in range(n_frames)]
    x = np.concatenate(frames)
    nseg = int(num.fs / RBW)  # 500 samples -> ~1 kHz RBW
    f, p = sig.welch(x, fs=num.fs, nperseg=nseg, noverlap=nseg // 2,
                     window="hann", return_onesided=False, detrend=False)
    order = np.argsort(f)
    f, p = f[order], p[order]  # PSD in power/Hz
    # absolute dBm per 1 kHz, normalizing total mean power to 27 dBm
    ptot = np.trapezoid(p, f)
    p_dbm_1khz = 10 * np.log10(p * RBW / ptot + 1e-30) + TX_POWER_DBM
    return f, p_dbm_1khz


def obw99(f: np.ndarray, p_dbm: np.ndarray) -> float:
    p = 10 ** (p_dbm / 10)
    c = np.cumsum(p)
    c /= c[-1]
    lo = f[np.searchsorted(c, 0.005)]
    hi = f[np.searchsorted(c, 0.995)]
    return hi - lo


def mask_abs(offsets_hz: np.ndarray) -> np.ndarray:
    """Absolute limit (dBm/1 kHz) vs offset beyond the band edge."""
    return np.clip(0.0 - 180e-6 * offsets_hz, -36.0, 0.0)


def check(f, p_dbm, edge_hz=125e3):
    """Worst margin (limit - psd, dB; negative = violation) per mask point."""
    pts = {}
    for off in (0, 20e3, 50e3, 100e3, 200e3, 400e3):
        lim = mask_abs(np.array([off]))[0]
        val = -1e9
        for s in (+1, -1):
            fx = s * (edge_hz + off)
            val = max(val, np.interp(fx, f, p_dbm))
        pts[off] = (val, lim, lim - val)
    return pts


def main():
    RESULTS.mkdir(exist_ok=True)
    configs = [
        ("raw (no shaping)", dict(window_len=0, use_tx_filter=False), NUM),
        ("WOLA nw=2 (4us)", dict(window_len=2, use_tx_filter=False), NUM),
        ("WOLA nw=4 (8us)", dict(window_len=4, use_tx_filter=False), NUM),
        ("FIR only", dict(window_len=0, use_tx_filter=True), NUM),
        ("FIR + nw=2 (default)", dict(window_len=2, use_tx_filter=True), NUM),
        ("FIR + nw=2, 60 occ", dict(window_len=2, use_tx_filter=True),
         Numerology(kmax=30)),
    ]
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 5.5))
    report = []
    for name, kw, num in configs:
        tx = Transmitter(num, **kw)
        f, p = tx_psd(tx, num)
        pts = check(f, p)
        bw = obw99(f, p)
        worst = min(m for _, _, m in pts.values())
        report.append((name, bw, pts, worst))
        ax.plot(f / 1e3, p, lw=0.8, label=f"{name} (OBW99 {bw/1e3:.0f} kHz)")
        print(f"{name:24s} OBW99={bw/1e3:6.1f} kHz  worst margin {worst:+6.1f} dB")
        for off, (val, lim, m) in pts.items():
            print(f"    edge+{off/1e3:5.0f} kHz: psd {val:7.1f} lim {lim:6.1f} "
                  f"margin {m:+6.1f} dB")

    fedge = np.linspace(0, 400e3, 200)
    for s in (+1, -1):
        ax.plot(s * (125e3 + fedge) / 1e3, mask_abs(fedge), "k--", lw=1.5,
                label="EN 300 220-2 Table 9 mask" if s > 0 else None)
    ax.axvline(-125, color="k", alpha=0.3)
    ax.axvline(125, color="k", alpha=0.3)
    ax.set_xlim(-330, 330)
    ax.set_ylim(-80, 15)
    ax.set_xlabel("offset from 869.525 MHz channel center [kHz]")
    ax.set_ylabel("PSD [dBm / 1 kHz] at 27 dBm mean ERP")
    ax.set_title("TX spectrum vs band-edge mask (N=128, fs=500 kHz)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    fig.savefig(RESULTS / "tx_spectrum.png", dpi=130)
    print(f"wrote {RESULTS / 'tx_spectrum.png'}")


if __name__ == "__main__":
    main()
