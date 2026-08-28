# OFDM numerology & FEC investigation — RESOLVED 2026-08-25

Working document for the PHY design session. Inherits `system_spec.md` and
`digital_spec.md`. All **TBD**s from the starter version are now resolved; the
locked parameter set is in **Session results** at the bottom. Supporting
artifacts produced this session:

- `docs/link_budget.md` — full link budget with arithmetic
- `docs/regulatory_notes.md` — EN 300 220-2 / Fribruksforskriften findings (parallel session)
- `sim/` — Python floating-point golden model (see `sim/README.md`), 21 passing
  sanity tests, BER/BLER curves and TX-spectrum-vs-mask results in `sim/results/`

## Fixed constraints (unchanged)

- Channel: 869.400–869.650 MHz, **250 kHz**, 500 mW ERP, 10% TX duty (TDD policy in
  the Sapphire scheduler; datapath is full-duplex-capable for future FDD).
- Link: ~2 km, **NLOS**, stationary ends, directional antennas, target 15–20 dB SNR.
- Converters: fixed **25 MSPS**, zero-IF I/Q. Modem baseband rate = 25 MHz / R.
- Both ends free-run on 0.5 ppm 100 MHz TCXOs. Worst-case end-to-end CFO:
  2 × 0.5 ppm × 869.4 MHz = ±869.4 Hz ≈ **±870 Hz** *(re-derived, confirmed)*.

## Framing — CONFIRMED, updated by regulatory findings

**1 Mbps = burst PHY rate**; ~100 kbps one-way average under 10% duty. The
regulatory investigation (docs/regulatory_notes.md §1) settled the fine print:
10% = **360 s TX per rolling hour per transmitter**, whole-band observation,
gaps < 5 ms merge into one transmission, no per-burst cap (36 s advisory).
**Update:** the "LBT to exceed 10%" idea is dead — EN 300 220-2 polite spectrum
access caps at 100 s/h per 200 kHz (≈2.8%), *stricter* than plain duty for a
full-band signal. Plain 10% is the operative regime; LBT remains a possible
coexistence feature only, needing no PHY change.

## Physics groundwork — RESOLVED

- **Delay spread** *(citations found)*: measured RMS delay spreads at ~900 MHz:
  Cox, "Delay Doppler characteristics of multipath propagation at 910 MHz in a
  suburban mobile radio environment," IEEE Trans. AP-20, 1972 — suburban NJ,
  typical rms 0.2–0.5 µs, worst ~2 µs. COST 207 channel models: Rural 0.1 µs,
  Typical Urban ~1.0 µs, Bad Urban ~2.5 µs, Hilly Terrain ~5 µs with discrete
  echoes out to ~17 µs. Erceg/SUI (IEEE 802.16.3c-01/29r4): SUI-1..6 rms
  0.11–5.2 µs omni, *substantially reduced with directional CPE antennas*
  (SUI's own antenna correction). For a 2 km directional fixed link: expect
  **rms ≤ 1 µs, max excess ≤ ~5 µs**; hilly-echo scenarios are the tail risk.
  → CP 16 µs gross (8 µs effective after windowing+timing backoff) covers the
  expected case; a CP=32 µs fallback mode exists if field measurements demand
  it (−5.6% rate). Verified in sim: 1 µs rms TDL passes at MCS3/30 dB.
- **CFO**: ±870 Hz = 22.3% of the chosen Δf = 3906.25 Hz. The lag-32 STF
  autocorrelator is unambiguous to ±fs/64 = ±7.8 kHz (9× margin) so no
  integer-CFO search is needed; LTF fine estimate lands within a few Hz
  (sim: |error| < 1 Hz at 35 dB SNR). Doppler ≈ 0; pilots track the residual.
- **Phase noise**: negligible for the LMX2582 (~50 fs integrated ≈ milli-degrees
  at 869 MHz). The long 256 µs symbol *is* PN-sensitive in principle: the sim
  shows a 50 Hz Lorentzian linewidth (16° intra-symbol wander) destroys 64-QAM,
  while 1 Hz (2.3°) — still ≫ reality — costs nothing. CPE correction from
  pilots implemented and kept (cheap insurance).
- **Zero-IF**: DC subcarrier nulled. **±1 carriers kept as data by default** —
  a digital DC-tracking notch on a static link can be ≪ Δf/2 wide; a config
  bit (`null_dc_adjacent`) exists to null ±1 (costs 3.8% rate) if bring-up
  shows the DC servo / 1/f corner reaching ~±4 kHz. Decide on hardware. I/Q
  imbalance: factory TX→RX loopback cal remains the plan (open, not in v1 sim).
- **PAPR**: v1 = pure back-off, PA sized for mean-ERP operation (see
  `docs/link_budget.md` — TX antenna gain directly reduces required PA power:
  ~20 dBm avg with a 9 dBi antenna, +~10 dB peak headroom). Clip+filter
  deferred; it mainly matters for the pre-2027 peak-detector ERP reading
  (link_budget "ERP measurement scenario") and PA cost, not for closing the link.

## Numerology — RESOLVED (all numbers re-derived)

Exact values, fs = 25 MHz / R:

| | A: "802.11a÷16" | B: 128-pt ("as drawn") | C: fine spacing | **B-56 (chosen)** | A′: 64-pt fallback |
|---|---|---|---|---|---|
| R (=25M/fs) | 80 = 2⁴·5 | 50 = 2·5² | 64 = 2⁶ | **50** | 80 |
| fs | 312.5 kHz | 500 kHz | 390.625 kHz | **500 kHz** | 312.5 kHz |
| N | 64 | 128 | 128 | **128** | 64 |
| Δf | 4882.8125 Hz | 3906.25 Hz | 3051.758 Hz | **3906.25 Hz** | 4882.8125 Hz |
| Tu | 204.8 µs | 256 µs | 327.68 µs | **256 µs** | 204.8 µs |
| Occupied (data+pilot) | 52 (48+4) | 64 (60+4) | 80 (76+4) | **56 (52+4)** | 48 (44+4) |
| Occupied span | 253.9 kHz | 250.0 kHz | 244.1 kHz | **218.75 kHz** | 234.4 kHz |
| Guard to band edge | < 0 | ~0 | 2.9 kHz | **15.6 kHz (4Δf)** | 7.8 kHz |
| CP | 12.8/25.6 µs | 8/16 µs | 20.5 µs | **16 µs (8 smp)** | 12.8 µs |
| CFO/Δf (±870 Hz) | 17.8% | 22.3% | 28.5% | **22.3%** | 17.8% |
| 64-QAM r3/4 rate | 993 kbps | 993 kbps | ~1.0 Mbps | **860 kbps** | 910 kbps |
| Regulatory verdict | **fails OBW** | **fails mask/drift** | shape OK, tiny guard | **passes, +20 dB margin** | passes (est.) |

Regulatory input (docs/regulatory_notes.md §2.1): 99% OBW must sit inside the
band *including* ±~1 kHz TCXO drift, and the band-edge mask needs ≥ −21 dB
(rel. in-band PSD) at edge+100 kHz, −39 dB at edge+200 kHz. That killed A and
B-as-drawn outright and forces TX spectral shaping on everything else.

**Golden-model spectrum measurements** (sim/run_spectrum.py, Welch 1 kHz RBW,
27 dBm mean ERP, worst mask margin over all Table 9 points):

| TX shaping (B-56) | OBW99 | Worst mask margin |
|---|---|---|
| none (raw CP-OFDM) | 223 kHz | **−12.0 dB (FAILS at edge+200 kHz)** |
| WOLA crossfade 4 µs | 222 kHz | −8.0 dB (fails) |
| WOLA crossfade 8 µs | 222 kHz | +2.9 dB (marginal) |
| 59-tap band-edge FIR | 222 kHz | +19.8 dB |
| **FIR + 4 µs WOLA (chosen)** | **222 kHz** | **+20.1 dB** |
| FIR + WOLA, 60-carrier ext. mode | 236 kHz | +14.7 dB |

**Decision — primary: "B-56"**: R=50, fs=500 kHz, N=128, Δf=3906.25 Hz,
56 occupied carriers (±1..±28, DC null), 4 pilots, CP 8 samples = 16 µs,
TX shaping = small band-edge FIR (remez, passband ±111.7 kHz, stopband
145 kHz+) + 2-sample raised-cosine WOLA crossfade + 32-sample burst power
ramps (transient-power rule). Why B-56 over the others:

- R=50 = CIC÷25 + halfband÷2 (or CIC÷10 + compensating FIR÷5) — clean chain;
  fs/4 relationship to nothing needed; 2.13× oversampling of the occupied band
  gives the band-edge FIR a comfortable transition band (a big part of why the
  mask margin is +20 dB).
- N=128 radix-2 FFT at 500 kSPS is trivial (one butterfly, ~³/₄ µs per
  transform at 100 MHz fabric clock — >300× real-time headroom).
- 2 µs sample granularity gives CP options 8/16/24/32 µs; 16 µs = 5.9%
  overhead against a 4–16 µs delay-spread target.
- CFO at 22.3% of Δf is comfortably inside the preamble estimator's range
  (no integer-CFO stage), verified end-to-end in sim at full ±870 Hz.
- C was rejected: 28.5% CFO fraction eats sync margin, 327.7 µs symbols are
  ~2× more phase-noise/latency-sensitive, guard only 2.9 kHz ≈ 1Δf, and its
  extra ~15% rate does not survive adding a realistic guard anyway.

**Extended mode "B-60"** (config, not default): 60 occupied (±1..±30, 56 data),
same everything else. Mask-verified in-model at +14.7 dB margin, OBW99 236 kHz
(+2 kHz drift < 250 kHz ✓). Gives 926 kbps @ 64-QAM r3/4, **1029 kbps @ r5/6 —
this is the 1 Mbps mode**. Gate on a hardware spectrum-analyzer measurement
(model excludes PA nonlinearity/LO spurs); default build ships B-56.

**Fallback: "A′"** (if N=128 ever proves painful in HDL — not expected):
R=80, fs=312.5 kHz, N=64, 48 occupied (44 data), CP 4 smp = 12.8 µs,
910 kbps @ 64-QAM r3/4. Same architecture, different constants.

## Pilot & preamble design — RESOLVED

**Preamble** (1.088 ms total, ~7% of a max-length frame):

```
STF: 8 × 32-sample repetition (512 µs) — built from every-4th-carrier QPSK
LTF: 32-sample CP + 2 × 128-sample known symbol (576 µs) — ±1 on all 56 carriers
```

- **Schmidl&Cox-class chosen over CAZAC/Zadoff-Chu.** Rationale: the S&C
  autocorrelation metric |P|/R is a *ratio* — AGC-state-independent and
  threshold-stable pre-calibration; the detector is a delay line + conjugate
  multiplier + moving sum (tiny HDL); and coarse CFO falls out of the same
  correlator phase for free (lag 32 → unambiguous to ±7.8 kHz ≫ ±870 Hz, so
  no integer-CFO search stage — this is where the "not much finer spacing"
  constraint pays off). A ZC preamble gives a sharper raw timing peak but
  needs a full-rate matched filter, is CFO-shift-sensitive, and buys nothing
  here because **fine timing comes from cross-correlating the known LTF**
  (S&C's plateau ambiguity never enters). Fine CFO from the LTF repetition
  (lag 128, range ±1.95 kHz, fine variance). Channel: LS estimate from the two
  averaged LTF symbols (+3 dB estimation SNR), one-tap per-carrier EQ.
- **Pilots: 4 comb pilots at ±7, ±21** (802.11a geometry), PRBS7 polarity.
  On a static, preamble-estimated channel they only need to carry
  common-phase-error / residual-CFO tracking — sparse is correct. No channel
  re-interpolation from pilots in v1 (frames are ms-scale, channel is static
  over a frame by orders of magnitude).
- **DC null: yes, always. ±1 carriers: data by default**, `null_dc_adjacent`
  config bit reserved (see zero-IF item above) — open choice pending hardware
  bring-up measurement; recommendation is to keep them unless the measured
  DC-notch corner exceeds ~500 Hz.

## FEC — RESOLVED

Comparison at our operating point (BLER ~1e-2, 300–1500 B frames, Topaz
TZ170 4-input-LUT fabric):

| | K=7 conv + soft Viterbi | tail-biting conv | 802.11n LDPC (648–1944) | conv + RS(255,223) |
|---|---|---|---|---|
| Gain vs uncoded @ r1/2 | ~5.5 dB | same | +1.5–2.5 dB over conv | +1.5–2 dB over conv |
| LUTs (est.) | 4–8k (64 parallel ACS + traceback) | 6–10k (wrap-around passes) | 15–40k + control | +3–6k RS core over conv |
| BRAM / DSP | 2–4 BRAM / 0 DSP | similar | 10–30 BRAM / few DSP | +RS syndrome BRAM |
| Latency | < 1 OFDM symbol (traceback ~96 bits) | 2–3× Viterbi passes | fine (~µs class) | + RS block (2040 b) interleaving |
| Effort | 1–2 weeks, textbook | +wrap heuristics for ~0.3% rate gain | 4–8 weeks + hard verification | two codecs + interleaver |

**v1 choice: K=7 convolutional (133/171 octal) + soft-decision Viterbi,
punctured {1/2, 2/3, 3/4, 5/6}** — 802.11a-proven with the same puncturing,
fits the "sizing estimate ~20–40k LUTs whole-modem" budget, golden model
already implements and validates it. Tail-biting rejected (saves 6 bits/frame
≈ 0.25% at 300 B — pointless at our frame sizes). RS concatenation rejected
(its niche is covered better by the LDPC upgrade path). **LDPC is the v2
upgrade** (+~2 dB ≈ 26% range or one MCS step) — resource headroom exists on
the Tz170; it is effort-bound, not LUT-bound. Interleaving: per-OFDM-symbol
13/14-column block interleaver (no deep interleaving needed — channel is
static, and symbol-local interleaving keeps decode latency at one symbol).

**MCS ladder (defined in v1, adaptation deferred):** the SIG header carries a
4-bit MCS field from day one, so both ends can renegotiate per-frame. v1 runs
manually-selected / static MCS; closed-loop adaptation (RSSI/EVM-driven) is a
Sapphire-scheduler feature for later — no PHY change required.

| MCS | Modulation | Rate | B-56 burst rate | ~SNR @ BLER 1e-2 (sim, AWGN) |
|---|---|---|---|---|
| 0 | QPSK | 1/2 | 191 kbps | ~5 dB |
| 1 | QPSK | 3/4 | 287 kbps | ~8 dB |
| 2 | 16-QAM | 1/2 | 382 kbps | ~10.5 dB |
| 3 | 16-QAM | 3/4 | 574 kbps | ~14 dB |
| 4 | 64-QAM | 2/3 | 765 kbps | ~18 dB |
| 5 | 64-QAM | 3/4 | 860 kbps | ~20 dB |
| 6 | 64-QAM | 5/6 | 956 kbps | ~22 dB |

(B-60 extended mode: multiply by 56/52 → MCS6 = 1029 kbps.)

## Frame format — RESOLVED (sketch)

```
| ramp 64µs | STF 512µs | LTF 576µs | SIG 272µs | payload N × 272µs | ramp |
```

- **SIG**: 1 OFDM symbol, always QPSK r1/2 (most robust MCS): 52 bits =
  MCS(4) | length_bytes(12, max 4095) | flags(8) | CRC-8(8) | rsvd(14) | tail(6).
- **Payload**: scrambled (x⁷+x⁴+1), CRC-32 appended, tail-terminated,
  symbol-padded. 1500 B at MCS5 = 52 symbols → **15.5 ms airtime, ~91% of it
  payload symbols**. ACK-sized frames (≤ 8 B) ≈ 1.9 ms, preamble-dominated —
  acceptable at our duty budget (a full 10% hour ≈ 23k max-length frames).
- **Soft ramps** at burst start/end (EN 300 220-2 transient-power rule — no
  hard PA keying); implemented in the model as raised-cosine ramps over
  64 µs + a cyclic dummy tail.
- **ARQ/ACK**: fits the TDD schedule naturally — TX burst, turnaround, short
  ACK frame carrying a bitmap in its payload. Duty accounting: gaps < 5 ms
  merge bursts into one *transmission* but off-time still doesn't count
  toward the 360 s/h budget; ACK airtime is declared on one side's budget
  (regulatory_notes §1). Stop-and-wait first, selective-repeat later — MAC
  business, PHY provides per-frame CRC-32 + MCS signaling, nothing more.

## Impairment sim — RESOLVED (built and passing)

`sim/` golden model implements the full chain (see `sim/README.md`):
modulator → channel (AWGN, CFO, TDL multipath, Wiener phase noise, 12-bit
quantization) → receiver (S&C sync, CFO correction, LS EQ, CPE, soft demap,
Viterbi) — `python -m sim.run_ber` and `python -m sim.run_spectrum` produce
the curves in `sim/results/`; 21 pytest sanity tests pass, including:
ideal-channel zero-error at every MCS, full ±870 Hz CFO recovery, 1 µs-rms
multipath within CP, combined worst-case impairments + 12-bit quantization,
and graceful failure (no false "success") at low SNR. Not yet modeled: I/Q
imbalance, PA nonlinearity/clipping, DAC zero-order-hold + interpolation
chain images (all flagged for the fixed-point/HDL phase).

## Session results — locked parameter set

| Parameter | Value |
|---|---|
| Decimation / baseband fs | R = 50 → **500 kHz** (CIC÷25 + HB÷2) |
| FFT / Δf / Tu | **N = 128 / 3906.25 Hz / 256 µs** |
| CP | **8 samples = 16 µs** (effective ≥ 8 µs after 4 µs WOLA + 4 µs timing backoff); 32 µs config fallback |
| Occupied carriers | **56** = 52 data + 4 pilots (±7, ±21), DC null, ±1 active |
| Guard to band edge | 15.6 kHz per side; OBW99 = 222 kHz |
| TX shaping | ~59-tap band-edge FIR + 4 µs RC crossfade + 64 µs burst ramps → **+20 dB worst mask margin** (model) |
| FEC | **K=7 conv 133/171 + soft Viterbi**, punctured 1/2–5/6; LDPC = v2 |
| MCS ladder | 7 entries, QPSK r1/2 … 64-QAM r5/6 (191–956 kbps); SIG always QPSK r1/2 |
| Preamble | STF 8×32 smp + LTF 2×128 smp (1.088 ms); S&C detect + LTF fine sync |
| Frame | preamble | SIG (MCS/len/CRC-8) | payload (+CRC-32), max 4095 B |
| Link budget | closes 64-QAM r3/4 @ 2 km NLOS with 7–22 dB margin at expected excess loss (see docs/link_budget.md) |
| 1 Mbps status | 860–956 kbps in default B-56 mode; **1029 kbps in B-60 extended mode** (mask-verified in model, gated on HW spectrum measurement) |

**Open items (explicitly not locked):**

1. **B-60 extended mode enable** — needs a hardware spectrum measurement with
   the real PA (model shows +14.7 dB margin; PA regrowth will eat some).
   Recommendation: build B-56 default, keep B-60 a register setting.
2. **±1 carrier nulling** — measure DC-servo/1-f corner at bring-up;
   recommendation: keep active.
3. **Adaptive MCS algorithm** — deferred to Sapphire scheduler (hooks exist).
4. **I/Q imbalance strategy** — factory loopback cal vs pilot-based estimation;
   not yet in the model.
5. **CP 32 µs mode** — only if a field delay-spread measurement at the actual
   sites shows > ~8 µs excess delay (hilly-echo case).
6. **Clip+filter PAPR reduction** — v2, tied to the peak-vs-mean ERP detector
   question (docs/link_budget.md) and PA design.
