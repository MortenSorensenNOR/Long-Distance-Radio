# Regulatory notes — 869.400–869.650 MHz SRD band (Norway / CEPT)

Researched 2026-08-25 from primary sources. All clause citations were read directly
from the published PDFs (freely downloadable):

- **ETSI EN 300 220-1 V3.1.1 (2017-02)** — technical characteristics & measurement.
  <https://www.etsi.org/deliver/etsi_en/300200_300299/30022001/03.01.01_60/en_30022001v030101p.pdf>
  (No newer Part 1 exists as of writing.)
- **ETSI EN 300 220-2 V3.2.1 (2018-06)** — harmonised standard, non-specific SRD.
  <https://www.etsi.org/deliver/etsi_en/300200_300299/30022002/03.02.01_60/en_30022002v030201p.pdf>
- **ETSI EN 300 220-2 V3.3.1 (2025-03)** — new harmonised version, self-contained
  (no longer defers to Part 1 for requirements). Mandatory for presumption of
  conformity after **11 June 2027**.
  <https://www.etsi.org/deliver/etsi_en/300200_300299/30022002/03.03.01_60/en_30022002v030301p.pdf>
- **CEPT ERC Recommendation 70-03, edition February 2025** (Annex 1 band **h1.7**,
  Appendix 5). <https://docdb.cept.org/download/4635>
- **Fribruksforskriften** (FOR-2012-01-19-77), **§ 8 nr. 19** (the quoted rule) plus
  § 2 (definitions) and § 3 (non-protected basis).
  <https://lovdata.no/dokument/SF/forskrift/2012-01-19-77>

Unless stated otherwise, clause numbers below are from **EN 300 220-2 V3.3.1**,
with the V3.1.1/V3.2.1 equivalent in parentheses where it differs.

---

## 1. Summary table of hard limits

| Parameter | Limit | Source (clause) |
|---|---|---|
| Frequency band | 869.400–869.650 MHz (Permitted Frequency Band, 250 kHz) | Fribruksforskriften § 8 (19); EN 300 220-2 V3.3.1 Table 4 / Annex B band **O** (V3.2.1 Annex B band **P**); ERC 70-03 Annex 1 band **h1.7** |
| Max radiated power | **500 mW = 27 dBm e.r.p.** (relative to half-wave dipole) | same three sources; e.r.p. definition Fribruksforskriften § 2; measurement EN 300 220-2 V3.3.1 §§ 4.4.1, 5.4.1 (V3.1.1 § 5.2) |
| PSD limit | **None for this band** (PSD limits apply only to bands I, W or NRIs that specify one) | V3.3.1 § 4.4.2.1 |
| Duty cycle | **≤ 10 %**, Tobs = **1 hour**, Fobs = the permitted frequency band, **per transmitter** → **≤ 360 s TX-on per hour per device** | V3.3.1 § 4.4.3.2 (V3.1.1 § 5.4.1); ERC 70-03 Appendix 5; Fribruksforskriften § 2 («en enkelt radiosender») |
| Per-transmission on-time (plain duty-cycle regime) | **No binding limit** in EN 300 220-2 for band O. ERC 70-03 Appendix 5 Table 22 gives an **advisory** max on-time of **36 s** for the ≤ 10 % category | V3.3.1 Table 4 (no Ton/Toff entry for band O); ERC 70-03 App. 5 Table 22 |
| Disregard time (gap that still counts as one transmission) | TDisregard declared by manufacturer, **≤ 5 ms** | V3.3.1 § 3.1 + Annex G declaration («TDisregard ≤ 5 ms»); V3.1.1 Table 48 note 2 |
| Polite spectrum access (alternative to duty cycle) | CCA ≥ **160 µs**; dead time ≤ **5 ms**; Ton_max **1 s** single TX / **4 s** dialogue; Toff_min **100 ms** on same frequency; **Tcum_on ≤ 100 s per hour per 200 kHz** of spectrum | V3.3.1 § 4.6.3.2 Table 18 (V3.1.1 § 5.21.3.1 Table 48) |
| CCA threshold (for 100–500 mW e.r.p.) | ≤ Rx-sensitivity limit + **11 dB**; sensitivity limit S = 10·log10(OCW/kHz) − 117 dBm → for OCW = 250 kHz: S ≤ **−93 dBm**, CCA threshold ≤ **−82 dBm** (at 0 dBd antenna gain; adjust for actual gain) | V3.3.1 § 4.6.2.3 Table 17 + § 4.5.1.3 Table 11 (V3.1.1 Table 45) |
| Max occupied bandwidth | **250 kHz** («the whole band»); OBW = **99 %-power bandwidth** (β/2 = 0.5 % per side) | V3.3.1 § 4.4.4, Table 4 band O (V3.1.1 § 5.6) |
| Frequency containment | 99 % OBW must lie **entirely inside the Operating Channel over the whole environmental profile** (i.e. including TX frequency drift), and the OC inside the PFB | V3.3.1 § 4.4.5.3 Table 6 (V3.1.1 § 5.6.2) |
| OOB mask, operating channel | 0 dBm/1 kHz at fnom ± 0.5·OCW, falling **linearly (in dB vs Hz)** to −36 dBm/1 kHz at fnom ± 2.5·OCW | V3.3.1 § 4.4.6.3 Table 7 (V3.1.1 § 5.8.2 Table 15) |
| **Band-edge mask** (the binding one here) | **0 dBm/1 kHz at 869.400 and 869.650**; then linear slope **180 dB/MHz** (= 36 dB over 200 kHz) to **−36 dBm/1 kHz** at edge ± 200 kHz; −36 dBm/1 kHz out to ± 400 kHz | V3.3.1 § 4.4.8.3 Table 9 (V3.1.1 Table 15, where beyond ±400 kHz the ref BW becomes 10 kHz) |
| Spurious domain (TX on) | ≤ **−36 dBm** below 1 GHz, ≤ **−30 dBm** above 1 GHz, ≤ **−54 dBm** in protected broadcast/PMR bands (47–74, 87.5–118, 174–230, 470–790 MHz) | V3.3.1 § 4.3.1.3 Table 5 (V3.1.1 § 5.9.2 Table 19) |
| Spurious (standby/RX) | ≤ −57 dBm below 1 GHz, ≤ −47 dBm above 1 GHz | same |
| Transient power (keying clicks) | Peak ≤ **0 dBm/1 kHz** within ±400 kHz of fnom, ≤ **−27 dBm** beyond, during TX on/off ramps | V3.3.1 § 4.4.9.3 Table 10 |
| Receiver requirements | V3.2.1: RX blocking at "category 2" limits mandatory. V3.3.1 (mandatory ≥ 2027-06-11): full RX set — sensitivity (≤ −93 dBm @ 250 kHz OCW if using PSA, ≤ −60 dBm otherwise), dynamic range, adjacent selectivity, blocking | V3.2.1 § 4.x; V3.3.1 § 4.5 |

### Duty cycle — fine print (all verified)

- **Definition**: DC = Ton_cum / Tobs over Fobs; Tobs = 1 h, Fobs = the permitted
  frequency band unless a band entry says otherwise (V3.3.1 § 4.4.3.2). Band O
  specifies nothing extra, so: **≤ 360 s cumulative TX per rolling hour**.
- **Per transmitter/device**: ERC 70-03 App. 5 ("'on' time of a *single transmitter
  device*") and Fribruksforskriften § 2 («'på'-tiden for en enkelt radiosender»).
  Each end of our TDD link has its own independent 10 % budget.
- **What counts as on-time**: measurement is a power-vs-time record; everything
  above −26 dBc from burst start to burst stop counts (V3.3.1 § 5.4.3.4 Table 35).
  **Preambles, headers, pilots — all of it counts.** Emissions separated by gaps
  < TDisregard (≤ 5 ms) are one transmission.
- **ACKs**: the responder's on-time is real on-time, but for conformance it is
  declared **once** — either in the initiator's or the responder's duty-cycle
  accounting, not both (V3.3.1 § 5.4.3.1). This is an accounting rule, not a
  free pass; the intent note says it must not let a device exceed 10 %.
- **Assessment period**: "the most active hour in normal use", where normal use
  covers 99 % of lifetime transmissions (V3.3.1 § 5.4.3.1). Setup/commissioning/
  maintenance excluded.

### Polite spectrum access — how much relief does it actually give?

**Surprise: for this band and a wideband signal, none — it is *stricter* than the
10 % duty cycle.** Table 18 caps cumulative on-time at **100 s/hour per 200 kHz
portion of spectrum (≈ 2.8 %)**. The escape hatch (note to Table 18: "longer
accumulated transmission time is possible by implementing more AFA channels")
does not help us: the whole permitted band is 250 kHz and our signal occupies
essentially all of it, so there are no additional AFA channels to hop to. A
~250 kHz OFDM carrier overlaps every 200 kHz portion of the band, so the strict
reading is 100 s/h total.

Consequently the Fribruksforskriften sentence allowing > 10 % "with interference
mitigation at least equivalent to harmonised-standard techniques" is a dead end
for this design: the harmonised-standard technique (LBT+AFA per § 4.6) buys
2.8 %/h per 200 kHz, not more than 10 %. **Design conclusion: operate under the
plain 10 % duty-cycle regime (360 s/h per device); implement LBT only if ever
useful for coexistence, not for throughput.**

---

## 2. Implications for our OFDM design

### 2.1 Band occupancy / numerology (feeds `ofdm_investigation.md` candidates)

A single modulated signal **may** occupy the full 250 kHz (max OBW = "the whole
band", Table 4 band O). But three separate requirements bound the edges:

1. **99 % OBW inside the OC/PFB including frequency drift** (§ 4.4.5.3): with our
   0.5 ppm TCXOs, TX drift is ±435 Hz (±0.5 ppm at 869.5 MHz) over temperature,
   more with aging — budget ≈ ±1 kHz per edge.
2. **Band-edge mask 0 dBm/1 kHz at 869.400/869.650** (Table 9): at full power the
   in-band mean PSD is 27 dBm − 10·log10(244…250 kHz / 1 kHz) ≈ **+3 dBm/1 kHz**,
   so the TX spectrum must already be ≥ ~3 dB below its in-band PSD *at* the edge.
3. **The 180 dB/MHz slope beyond the edge** (Table 9). In absolute terms
   (and relative to the ≈ +3 dBm/1 kHz in-band PSD):

   | Offset beyond 869.400/869.650 | Limit (1 kHz RBW) | Relative to in-band PSD |
   |---|---|---|
   | 0 (at edge) | 0 dBm | −3 dB |
   | 20 kHz | −3.6 dBm | −6.6 dB |
   | 50 kHz | −9 dBm | −12 dB |
   | 100 kHz | −18 dBm | −21 dB |
   | 200 kHz | −36 dBm | −39 dB |
   | > 400 kHz (spurious domain) | −36 dBm abs. | — |

   Both adjacent segments are **alarm bands** (social/security alarms at
   869.200–869.250 — Norwegian trygghetsalarm, Fribruksforskriften § 22 — and
   alarms at 869.650–869.700), which is why the edges are hard-protected;
   expect zero tolerance here.

**Verdict on the three candidates** (this paragraph is our derivation, not from
the standards):

- **Candidate A (~254 kHz occupied)**: occupied span > 250 kHz → the 99 % OBW
  cannot fit inside a ≤ 250 kHz operating channel. **Non-compliant, ruled out.**
- **Candidate B (250.0 kHz "exact fit")**: outermost subcarrier centers land
  ~2 kHz from the band edges at full PSD; the mask point at the edge (−3 dB rel.
  in-band) is immediately violated by the outer carriers' own main lobes, and
  there is zero margin for the ±1 kHz drift requirement of § 4.4.5.3.
  **Non-compliant as drawn** — nulling outer carriers to fix it turns it into a
  candidate-C-like numerology anyway.
- **Candidate C (~244 kHz occupied, ~3 kHz guard per side)**: the edge point
  (−3 dB) is satisfiable, but plain rectangular-pulse CP-OFDM sidelobes decay
  far too slowly to meet −21 dB rel. at 100 kHz and −39 dB rel. at 200 kHz
  offset (raw CP-OFDM is typically only ~−25 to −30 dBr at offsets comparable
  to the signal bandwidth). **Compliant only with TX spectral shaping.**

**Design constraints to adopt:**

- Keep the outermost subcarrier **center** ≥ ~1–1.5 subcarrier spacings inside
  the band edge (≥ 3–5 kHz guard per side), i.e. occupied span ≤ ~244 kHz.
  Candidate C's geometry is the right shape; re-derive exact carrier count when
  Δf is locked.
- Implement **time-domain windowing (WOLA / raised-cosine overlap)** of at least
  a few samples per symbol, and/or a sharp digital TX filter, targeting ≥ 45 dB
  attenuation 200 kHz from band center ±122 kHz. The analog TX BPF/SAW helps in
  the spurious domain but is far too wide to help at 50–200 kHz offsets.
- **Ramp TX power up/down** over ≥ a few symbol-lengths' worth of samples — hard
  keying violates the transient-power limit (Table 10) and would splatter into
  the alarm bands.
- Null DC (zero-IF hygiene, already planned) — no regulatory impact, the mask
  cares only about edges.
- Frequency-plan margin: reserve ±1 kHz per edge for TCXO tolerance + aging so
  the *measured* OBW under extreme conditions stays inside the OC (§ 4.4.5.3).

### 2.2 Duty cycle → MAC/scheduler constraints

- Budget: **360 s TX per rolling hour per device** (each direction separately).
  At 1 Mbps burst PHY rate → ~45 MB/h/direction ≈ 100 kbps average, as already
  assumed in `ofdm_investigation.md`. That assumption is **confirmed**.
- Count *everything* the PA radiates: preamble, sync, headers, ACKs. Gaps < 5 ms
  inside a frame exchange still count as one transmission (relevant if we do
  fast turnaround TDD: a < 5 ms RX slot between two TX bursts merges them into
  one "transmission" for accounting — fine, but the off-time inside it is still
  off-time for the Ton_cum sum, since Ton is measured burst-by-burst above
  −26 dBc).
- No per-burst on-time cap applies in the plain duty regime, but keeping bursts
  ≤ 36 s honors the advisory ERC 70-03 App. 5 figure trivially (our frames are
  ms-scale).
- Scheduler should enforce the budget over a **sliding 1-hour window**, per node.

### 2.3 LBT/AFA parameters (if ever implemented — for coexistence, not throughput)

- CCA listen ≥ **160 µs** (measure mean power over the interval); start TX within
  ≤ **5 ms** of a clear CCA (dead time), else re-listen.
- CCA threshold ≤ **−82 dBm** at 0 dBd antenna; with a directional RX antenna of
  gain G dBd the threshold at the front end must be lowered by G (Table 17 note).
  With ~10 dBi (7.85 dBd) antennas: ≤ ~−90 dBm — easily within our RX chain's
  ability but it must be measured over the *whole* 250 kHz channel.
- On busy: defer a random multiple of a declared deferral unit; or AFA (moot,
  single channel).
- Ton ≤ 1 s per transmission, ≤ 4 s per dialogue; Toff ≥ 100 ms on the same
  frequency after each transmission; cumulative ≤ 100 s/h per 200 kHz.
- PHY note: nothing in the PHY needs to change to add LBT later — it is purely
  scheduler + an RSSI integration over ≥ 160 µs. The existing plan (design MAC so
  LBT can be added) is sufficient.

### 2.4 ERP → PA output math

- Fribruksforskriften § 2 defines e.r.p. **relative to a lossless half-wave
  dipole** → **ERP = EIRP − 2.15 dB** confirmed. 27 dBm ERP = 29.15 dBm EIRP.
- Conducted conformance: P_erp = P_conducted(at antenna port) + antenna gain in
  **dBd** (V3.3.1 § 5.4.1.2.3 Table 32 note; V3.1.1 § 5.2.2.1.2). Therefore:

  **P_PA_out ≤ 27 dBm − G_ant[dBd] + L_cable[dB]**  (G[dBd] = G[dBi] − 2.15)

  | TX antenna | P at antenna port | PA out with 1 dB cable/switch loss |
  |---|---|---|
  | 0 dBd (dipole) | ≤ 27 dBm | ≤ 28 dBm |
  | 5 dBi (2.85 dBd) | ≤ 24.2 dBm | ≤ 25.2 dBm |
  | 10 dBi (7.85 dBd) | ≤ 19.2 dBm | ≤ 20.2 dBm |
  | 12 dBi (9.85 dBd) | ≤ 17.2 dBm | ≤ 18.2 dBm |

- **No separate PSD limit** for this band (§ 4.4.2.1), so concentrating the
  500 mW in 244 kHz is fine.
- **Peak vs mean — version-dependent (important for OFDM PAPR):**
  - Under EN 300 220-1 V3.1.1 § 5.2.2 (the method behind the currently-cited
    V3.2.1): "In the case of non-constant envelope modulation, a **peak detector**
    shall be used." Read literally, 27 dBm ERP caps something close to the OFDM
    **peak envelope power** → with ~10 dB PAPR the mean ERP would be ~17 dBm.
  - Under EN 300 220-2 V3.3.1 § 5.4.1 the ERP is measured "until a stable
    reading" with the general rule "unless stated otherwise, an **RMS detector**
    shall be used" (§ 5.2.x) → effectively **mean power**, the sane reading for
    OFDM, and the version that governs from June 2027.
  - Design recommendation: size the link budget with **mean ERP = 27 dBm**
    (V3.3.1 reading), but keep the PA's actual clipping point and back-off
    documented; if we ever want strict V3.2.1-era conformity the TX power knob
    must be able to drop ~PAPR dB. This also interacts with clip+filter vs pure
    back-off — clipping to ~7–8 dB PAPR both helps the older peak-reading *and*
    the PA, at the cost of EVM (fold into the golden-model impairment sim).

### 2.5 Receiver-side obligations (mostly relevant if aiming for real conformity)

- Current harmonised version (V3.2.1): RX **blocking** at category-2 limits is
  the only mandatory RX test.
- V3.3.1 (mandatory from 11 June 2027) adds sensitivity, dynamic range, adjacent
  selectivity etc. for all non-specific SRDs. If we implement LBT, RX sensitivity
  must be ≤ −93 dBm for a 250 kHz OCW (§ 4.5.1.3) — our planned LNA/NF easily
  clears this (thermal floor −120 dBm/250 kHz + reasonable NF and SNR).

---

## 3. Norway specifics

- **Fribruksforskriften § 8 nr. 19** is a verbatim national implementation of the
  EU/CEPT harmonised entry (EN 300 220-2 band O / ERC 70-03 h1.7 / EC Decision
  band 54): 500 mW e.r.p., ≤ 10 % sendetid, > 10 % only with mitigation
  equivalent to harmonised-standard techniques. **No Norwegian deviation found**
  for this sub-band — no channelization, no PSD limit, no indoor restriction.
- § 2 defines *sendetid* per single transmitter (matches ERC 70-03 App. 5) but
  does **not** state the observation period; EN 300 220-2 (which § 8 (19) invokes)
  supplies Tobs = 1 h.
- § 3: use is **license-exempt but unprotected** — no protection from other legal
  users, and must not degrade licensed services.
- Adjacent Norwegian allocations worth respecting: **trygghetsalarm (social
  alarm) 869.200–869.250 MHz (§ 22)** below, alarms 869.650–869.700 above —
  the band-edge mask is what protects them; do not shave the guard bands.
- The forskrift references "EN 300 220-2" **undated**; V3.2.1 is the version
  currently cited in the OJEU, V3.3.1 takes over 11 June 2027. Practical
  approach: design to V3.3.1 (it is the stricter/complete one and the near
  future), noting the ERP detector difference in § 2.4.

---

## 4. Not verified from primary sources / open items

- **Pro-rating of the PSA 100 s/h "per 200 kHz portion"** for a 250 kHz-wide
  signal: the standard's text ("per 200 kHz portion of spectrum per hour",
  Table 18) does not define portion boundaries or pro-rating. Strict reading
  used here: a full-band signal gets 100 s/h total. Not authoritative — but
  moot, since we choose the 10 % duty regime.
- **ETSI TS 103 060** (referenced measurement method for duty cycle in V3.1.1
  § 5.5.2.2) was not fetched; the duty-cycle accounting above is from
  EN 300 220-2 V3.3.1 § 5.4.3 directly, which is self-contained.
- **Legal status of self-built equipment for own use in Norway**: the
  radioutstyrsforskriften (FOR-2016-04-15-377, Norwegian RED implementation)
  governs producing/importing/selling; Nkom's guidance page on production/import/
  sale is silent on homebuilt-for-own-use, and the RED amateur exemption does not
  apply (869 MHz SRD is not an amateur band). Whether a one-off self-built device
  that is never placed on the market formally requires RED conformity assessment
  before being *put into service* in Norway is **unresolved** — if it matters,
  ask Nkom directly. The technical conditions of Fribruksforskriften § 8 (19)
  apply regardless.
- **Norway's cell in ERC 70-03 Appendix 1** (implementation matrix for h1.7)
  could not be reliably decoded from the PDF text layout (country columns
  misalign in text extraction). Fribruksforskriften § 8 (19) is direct primary
  evidence of implementation, so nothing hinges on it.
- **OFDM sidelobe/windowing numbers** in § 2.1 (raw CP-OFDM ~−25…−30 dBr at
  band-scale offsets; WOLA reaching the mask) are engineering estimates, not
  standard values — verify against the Python golden model's PSD with the mask
  points of Table 9 before locking the numerology.
- The **peak-vs-RMS ERP detector** discrepancy between EN 300 220-1 V3.1.1 and
  EN 300 220-2 V3.3.1 is reported as read; no ETSI clarification/TR reconciling
  the two was located.
