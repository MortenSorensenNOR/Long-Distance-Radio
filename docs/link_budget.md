# Link budget — 869.4 MHz, 2 km NLOS, 250 kHz channel

Session output 2026-08-25. Companion to `ofdm_investigation.md` (numerology) and
`docs/regulatory_notes.md` (mask/duty/ERP rules). All arithmetic shown; check it.

## Fixed inputs

| Quantity | Value | Note |
|---|---|---|
| TX power | 27 dBm ERP = **29.15 dBm EIRP** | 500 mW e.r.p.; EIRP = ERP + 2.15 dB (dipole→isotropic) |
| Frequency | 869.4 MHz | λ = c/f = 2.9979e8 / 869.4e6 = **0.3448 m** |
| Distance | 2 km | |
| Noise bandwidth | 250 kHz | full channel; per-subcarrier analysis not needed for budget |
| Thermal noise floor | −174 + 10·log10(250e3) = −174 + 53.98 = **−120.0 dBm** | |
| Required SNR, 64-QAM r3/4 | 18–20 dB | AWGN, BLER ≈ 1e-2, ~1500 B frames (802.11a-class receiver deltas) |

## Free-space path loss

FSPL = 20·log10(4πd/λ) = 20·log10(4π·2000 / 0.3448) = 20·log10(72 881) = **97.25 dB**

(Equivalent: 32.45 + 20·log10(869.4) + 20·log10(2) = 32.45 + 58.78 + 6.02 = 97.25 dB.)

## NLOS excess loss — literature

Empirical models, evaluated at f = 869.4 MHz, d = 2 km (my arithmetic, re-derivable
from the papers):

**Okumura–Hata** (M. Hata, "Empirical formula for propagation loss in land mobile
radio services," IEEE Trans. Veh. Technol., VT-29(3), 1980; based on Okumura's
Tokyo-area measurement campaigns, valid 150–1500 MHz, 1–20 km):

| base h_b / remote h_m | Urban | Suburban | Open/rural | Suburban excess over FSPL |
|---|---|---|---|---|
| 10 m / 2 m | 142.9 dB | 133.0 dB | 114.5 dB | **35.8 dB** |
| 15 m / 4 m | 135.0 dB | 125.2 dB | 106.7 dB | 27.9 dB |
| 30 m / 4 m | 130.3 dB | 120.4 dB | 101.9 dB | 23.2 dB |

Open/rural excess over FSPL: 5–17 dB across the same height range.

**Erceg et al.** ("An empirically based path loss model for wireless channels in
suburban environments," IEEE JSAC 17(7), 1999 — 95 macrocells, basis of the
IEEE 802.16 SUI models): terrain category B (intermediate), h_b = 10 m gives
γ ≈ 5.6, L(2 km) ≈ 140+ dB before height/frequency corrections — i.e. *worse*
than Hata suburban. Category C (flat, light tree density) lands ≈ 10 dB lower.
Lognormal shadowing σ = 8–10 dB about the median in both models.

**Caveats that pull the real number down for *this* link:** Hata/Erceg model a
low omni mobile buried in clutter, averaged over locations. A fixed installed
link with both ends elevated and *directional* antennas (a) sits at one point of
the shadowing distribution — you site the antennas until the link works, you
don't average — and (b) directivity suppresses off-boresight clutter paths
(documented in the SUI model's antenna-correction: a 32° antenna reduces both
excess loss spread and delay spread vs omni). ITU-R P.1411 short-range NLOS
measurements at UHF similarly span roughly 10–30 dB over free space at 1–2 km
depending on rooftop clearance.

**Adopted range: L_excess = 10–36 dB**, with 15–25 dB the expected operating
region for a sited suburban/rural link with elevated directional ends, and
35–36 dB the "Hata suburban, low antennas, bad siting" worst case.

## Antenna gains

- **TX gain does not add link margin** — ERP is capped at 27 dBm. TX directivity
  only reduces required PA output: P_PA = 27 dBm − (G_TX − 2.15 dB) + L_feed.
  With G_TX = 6/9/12 dBi: P_PA ≈ 23.2 / 20.2 / 17.2 dBm average (before
  switch/filter/cable loss, and before OFDM PAPR back-off — the PA must pass
  peaks ~8–10 dB above average, so 12 dBi TX antenna → ~0.5 W-peak-class PA
  instead of ~2 W-peak-class. That is the entire benefit.)
- **RX gain adds SNR dB-for-dB** (up to the point where external noise, not the
  LNA, sets the floor — at 869 MHz with an LNA-first chain, receiver noise
  dominates, so full credit is fair).

## System noise figure

LNA-first chain: SAW pre-filter insertion loss (~2–3 dB) *ahead* of the LNA adds
directly. NF_sys = L_SAW + NF_LNA + (following stages)/G_LNA. With a ~0.8 dB
LNA at 20 dB gain behind a 2.5 dB SAW: NF ≈ 3.5–4 dB realistic; parameterized
**NF = 3–6 dB** below. (If the SAW must stay in front for the 850–862 MHz
uplink-blocking requirement, NF < 3.5 dB is unlikely.)

## Budget

RX power: P_RX = EIRP − FSPL − L_excess + G_RX = 29.15 − 97.25 − L_excess + G_RX

SNR = P_RX − (−120.0 + NF) = **51.9 − L_excess + G_RX − NF** [dB]

SNR table at **NF = 4 dB** (for other NF, subtract (NF − 4)):

| L_excess ↓ \ G_RX → | 6 dBi | 9 dBi | 12 dBi |
|---|---|---|---|
| 10 dB (open, elevated) | 43.9 | 46.9 | 49.9 |
| 15 dB | 38.9 | 41.9 | 44.9 |
| 20 dB (expected) | 33.9 | 36.9 | 39.9 |
| 25 dB (expected, worse) | 28.9 | 31.9 | 34.9 |
| 30 dB | 23.9 | 26.9 | 29.9 |
| 36 dB (Hata suburban, h_b=10 m) | 17.9 | 20.9 | 23.9 |

## Conclusion

- **Does 1 Mbps burst close at 2 km NLOS? Yes, with margin, under expected
  conditions.** At the expected operating point (L_excess = 15–25 dB, G_RX =
  9 dBi, NF = 4 dB): SNR = 27–42 dB, i.e. **7–22 dB of margin** over the 20 dB
  needed for 64-QAM r3/4.
- **Fading margin:** the link is static; multipath fading is quasi-Rician and
  slow (moving objects inside the link). Design target: ≥ 8 dB margin at the
  top MCS, which holds for L_excess ≤ 24 dB (G_RX = 9, NF = 4). Shadowing is
  handled by siting, not margin.
- **Where it breaks:** full Hata-suburban excess (36 dB) with NF = 6 and only
  6 dBi RX gives SNR ≈ 15.9 dB — 64-QAM r3/4 fails, but 16-QAM r3/4 (needs
  ~14 dB) still closes → **574 kbps burst** (numerology B-56). The MCS ladder
  (see `ofdm_investigation.md`) degrades gracefully; the link only dies
  entirely (QPSK r1/2, ~5 dB required) below SNR ≈ 5 dB, i.e. L_excess ≳ 51 dB
  — deep-urban territory this link is not in.
- **Sensitivity summary:** required P_RX for 64-QAM r3/4 = −120 + 4 + 20 =
  **−96 dBm**; for QPSK r1/2 = **−111 dBm**.
- Antenna money goes on the **RX side** (both ends RX in TDD → both ends
  directional anyway, but the *reason* is RX SNR + PA cost reduction, not TX
  margin).

## ERP measurement scenario: mean vs peak detector (regulatory)

Per `docs/regulatory_notes.md` §2.4: EN 300 220-2 **V3.3.1** (mandatory from
June 2027) measures ERP with an RMS detector → **mean ERP = 27 dBm**, which is
what the table above assumes. The older EN 300 220-1 **V3.1.1** method reads
literally as a *peak* detector for non-constant-envelope modulation — under
that reading, OFDM with ~9–10 dB PAPR (or ~7–8 dB after clip+filter) would
force the **mean** TX power down by that amount:

| Scenario | Effective mean ERP | SNR table shift | 64-QAM r3/4 closes? |
|---|---|---|---|
| V3.3.1 mean-power (design basis) | 27 dBm | 0 dB | yes, L_excess ≤ ~37 dB |
| V3.1.1 peak, clip+filter to 8 dB PAPR | ~19 dBm | −8 dB | only for L_excess ≤ ~29 dB; 16-QAM ladder below that |
| V3.1.1 peak, pure back-off (10 dB PAPR) | ~17 dBm | −10 dB | only for L_excess ≤ ~27 dB |

Design consequence: **TX power is a runtime knob** (already required for AGC/
cal); if strict pre-2027 conformity is ever wanted, drop the knob by ~PAPR dB
and let the adaptive MCS ladder absorb the SNR loss. No hardware change.

Also note (same doc, §1): the 10 % duty regime is the operative one — LBT/AFA
polite access gives *less* airtime here (100 s/h), so no throughput relief is
assumed anywhere in this budget.
