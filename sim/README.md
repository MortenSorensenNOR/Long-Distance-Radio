# sim/ — floating-point golden model

Python reference implementation of the OFDM PHY locked in
`../ofdm_investigation.md` ("Session results", 2026-08-25). This model is the
behavioral reference the HDL will be verified against with cocotb: every block
here maps to a fabric block in `digital_spec.md`'s DSP pipeline, and the tests
in `tests/` are the seeds of the cocotb testbenches.

Dependencies: numpy, scipy (TX FIR design + Welch PSD), matplotlib (plots).
No project venv is required if these are installed system-wide; otherwise:

```
uv run --no-project --with pytest --with numpy --with scipy --with matplotlib \
    python -m pytest sim/tests
```

## Locked parameters (see params.py)

- fs = 25 MHz / 50 = 500 kHz, N = 128, Δf = 3906.25 Hz
- CP = 8 samples = 16 µs (2-sample WOLA crossfade + 2-sample RX timing
  backoff leave ≥ 8 µs effective multipath guard)
- 56 occupied carriers ±1..±28 (DC nulled), 4 pilots at ±7, ±21 → 52 data
- Extended mode: `Numerology(kmax=30)` → 60 occupied / 56 data (mask-verified)
- MCS ladder: QPSK–64QAM × K=7 conv code (133/171) r 1/2..5/6 (see MCS_TABLE)
- TX shaping: 59-tap band-edge FIR (remez, stop 145 kHz) + RC crossfade +
  32-sample burst power ramps — required by EN 300 220-2 Table 9, see
  `../docs/regulatory_notes.md` §2.1 and run_spectrum.py

## Layout

| File | Contents | Future HDL counterpart |
|---|---|---|
| `params.py` | numerology + MCS tables, PHY-rate helper | package constants |
| `fec.py` | conv encoder, puncturing, soft Viterbi | encoder / Viterbi core |
| `modem.py` | QAM map/LLR, interleaver, scrambler, pilots, preamble, SIG header, `Transmitter`, `Receiver` | mapper, framer, FFT datapath, sync |
| `channel.py` | AWGN, CFO, TDL multipath, Wiener phase noise, 12-bit quantization | cocotb impairment driver |
| `run_ber.py` | BER/BLER vs SNR curves → `results/` | — |
| `run_spectrum.py` | TX PSD vs EN 300 220-2 band-edge mask → `results/` | — |
| `tests/test_sanity.py` | pytest sanity suite (21 tests) | cocotb test list |

## Signal chain

```
TX: payload -> +CRC32 -> scramble(x^7+x^4+1) -> conv K=7 -> puncture
    -> 13/14-column block interleave (per symbol) -> Gray QAM
    -> carriers+pilots, DC null -> 128-IFFT -> +CP
    -> WOLA crossfade -> burst ramp -> band-edge FIR
    frame = STF(256) | LTF(32+2x128) | SIG(1 sym, QPSK r1/2) | payload syms

RX: STF autocorrelation (Schmidl&Cox metric, lag 32) -> detect + coarse CFO
    -> LTF cross-correlation fine timing -> LTF-repeat fine CFO
    -> LS channel estimate (2 LTF avg) + noise estimate -> per-carrier EQ
    -> pilot CPE derotation -> weighted max-log LLR -> deinterleave
    -> depuncture -> soft Viterbi -> descramble -> CRC32 check
```

Conventions worth knowing before writing HDL:

- LLR sign: llr > 0 means bit 0 more likely; erasure (punctured) = 0.
- Time signals are unit average power; `Numerology.ifft_scale` makes it so.
- The receiver's channel estimate absorbs the TX FIR and the timing backoff
  (deliberate: they cancel in the one-tap EQ).
- SNR in `channel.py` is referenced to the occupied bandwidth (≈219 kHz), so
  it lines up with `docs/link_budget.md` (250 kHz reference, <0.6 dB apart).

## Running

```
python -m sim.run_ber                  # BER/BLER curves, AWGN + impaired
python -m sim.run_ber --mcs 5 --frames 60 --channel impaired
python -m sim.run_spectrum             # TX PSD vs regulatory mask
python -m pytest sim/tests -q          # sanity suite
```

Outputs land in `sim/results/` (PNG + CSV). The "impaired" profile is the
worst-case operating point: ±870 Hz CFO (both TCXOs at 0.5 ppm limits), 1 µs
rms TDL multipath, 1 Hz Lorentzian phase noise (>> LMX2582 reality), 12-bit
ADC quantization at 12 dB backoff. Setting phase noise to 50 Hz is a known
kill switch for 64-QAM (16° intra-symbol wander over the 256 µs symbol) —
kept as a stress knob, not a realistic setting.
