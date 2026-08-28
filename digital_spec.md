# Digital board specification (control / ADC / DAC board)

Companion to `system_spec.md`. Captures the digital-side architecture decided 2026-08.
Open items are marked **TBD**.

## Part decisions

| Function | Part | Notes |
|---|---|---|
| FPGA | Efinix Topaz **TZ170J361I2** | ~$80. 161k LE, 544 DSP, 11.1 Mb BRAM, hard x16 LPDDR4 ctrl, 45 HSIO pairs @1.3 Gbps. 16 nm. |
| Soft CPU | Efinix **Sapphire** RISC-V SoC | Replaces the RP2350 from the original spec. Bare-metal/FreeRTOS first, Linux possible via BR2-Efinix. |
| Host bridge | FTDI **FT601Q-B** | USB 3.0 SuperSpeed → 32-bit/100 MHz FIFO. ~350–365 MB/s measured aggregate (shared half-duplex FIFO bus). Falls back to USB2 HS (~35 MB/s): control + decimated streaming only — firmware must detect negotiated speed and gate the raw tap. |
| USB-C **port A** | FT601Q-B only | Dedicated I/Q streaming port. Data-only; draws no power role (board runs from port B only, by design). |
| USB-C **port B** | utility port | Power (PD) + programming + console + management. |
| USB-C power | PD sink controller, STUSB4500-class, on port B | **TBD exact MPN.** Autonomous. Port B powers the board. |
| JTAG/console | FT4232H, copied from Efinix eval board schematic | Efinity programmer + Sapphire UART console work out of the box. |
| USB 2.0 hub | generic 2/4-port, on port B | ~$1.50, trivial layout. Feeds FT4232H + optional network branch. **TBD MPN.** |
| USB-Ethernet (opt.) | AX88772/LAN9500-class + FPGA-side 10/100 PHY | DNP footprint on port B hub. Inbox-driver plug-and-play NIC; magnetics-less PHY-to-PHY link to soft MAC + lwIP on Sapphire. **TBD MPNs.** |
| ADC | TI **ADS4222IRGCT** | Dual 12-bit 65 MSPS, run at 25 MSPS. DDR LVDS output mode (CMOS fallback selectable). Pin-compatible 14-bit upgrade: ADS4242. |
| DAC | ADI **AD9117** | Dual 14-bit 125 MSPS TxDAC, run at 25 MSPS. CMOS interface — see EMI section. |
| Clock divider | 2× discrete D-FF (74LVC1G74-class), ÷2→÷2 | See clocking. **TBD exact MPN** + LVDS fanout buffer MPN. |
| DRAM | x16 LPDDR4, single chip | **TBD MPN/density.** Capture buffers + optional Linux. Hard controller in J361 package. |

Sourcing rule: all MPNs to be sanity-checked against the JLC parts library before schematic capture; within-family substitutions (e.g. ADS4222→ADS4242) are acceptable on availability grounds.

## Clocking

Everything is an integer relationship of the one 100 MHz TCXO (clock board, 0.5 ppm).

```
clock board: TCXO → 1:4/1:8 fanout buffer → one clean 100 MHz copy per board
digital board:
  100 MHz in ─┬─ FPGA global clock input (fabric/DSP domains via PLL, e.g. 100 MHz DSP clock)
              └─ ÷2 → ÷2 (discrete FFs) → 25 MHz fs → LVDS fanout → ADC, DAC, mezzanine, FPGA
  FT601 supplies its own 100 MHz FIFO-bus clock (asynchronous domain)
  LPDDR4 hard controller: own domain, handled by Efinity
```

- **Fixed fs = 25 MSPS forever.** All rate changes happen in fabric (today: decimate to ~500 kSPS for the 250 kHz channel; future 8 MHz channels use lower decimation). One converter clock domain, one anti-alias design, "raw tap" always means the same thing.
- Rationale for ÷4 = 25: integer division of 100 MHz only (no fractional-N spurs); 0.8×fs ≈ 20 MHz usable complex BW at zero-IF covers the future 8 MHz channels with margin. (The earlier 32 MSPS ambition was dropped: not coherent with 100 MHz.)
- **One divider, then fan out** — a ÷4 wakes in one of 4 phases vs the 100 MHz, so ADC/DAC/mezzanine must share the same divided clock. Divider has an FPGA-GPIO reset for deterministic phase (MIMO / timestamp alignment insurance).
- Jitter budget: zero-IF means f_in ≤ a few MHz; SNR_jitter = −20log10(2π·f_in·t_j) gives >60 dB even at tens of ps. FF dividers add ~ps and division scales reference phase noise by −12 dB. No jitter cleaner needed.
- Clock-spur bonus: 25/100 MHz harmonics straddle the operating band (850, 875, 800, 900 MHz) — no discrete clock harmonic lands in 869.4–869.65 MHz. Data-dependent broadband noise is the residual concern (see EMI).
- CDC rule: all domain crossings via async FIFOs; fs↔DSP-clock crossings are 1:4 integer-related.

## Host interface & streaming

- Bidirectional raw I/Q at full rate is a hard requirement: 25 MSPS × 2 ch × 16 b = **100 MB/s per direction**, 200 MB/s aggregate under simultaneous RX+TX — fits FT601's ~350 MB/s aggregate; 12-bit packing (150 MB/s aggregate) is the margin lever.
- Raw tap is muxable pre/post decimation, both directions.
- Elastic buffering: BRAM FIFOs for streaming jitter; LPDDR4 for large capture/playback buffers (seconds of raw I/Q) and host-stall tolerance.
- Control channel multiplexed over the same FT601 link (dedicated endpoint/channel framing, **TBD protocol**). GbE (RGMII PHY + soft MAC) is an explicit later option, not in v1.

### Two-port USB architecture

- **Port A (streaming):** FT601 only, USB 3.0. Nothing else shares it — the
  zero-firmware streaming path stays isolated from everything experimental.
- **Port B (utility):** PD sink (powers the board) + USB 2.0 hub feeding the
  FT4232H (JTAG for Efinity + Sapphire console, schematic copied from the Efinix
  eval board) and a DNP'd network branch.
- **Decided:** port A alone leaves the board unpowered, by design — streaming
  without the control plane is meaningless, so port B (power + management) is
  a hard prerequisite for operation. No 5 V fallback from port A.

### Network-adapter requirement (1–10 Mbps)

The radio should be able to appear as a network adapter on the host. FTDI bridges
(FT601, FT4232H) are fixed vendor-class and can never present a USB network class, so:

- **v1 path:** host-side TAP/TUN daemon bridges a virtual NIC to an FT601 control
  channel on port A. Full functionality, requires installing our software.
- **plug-and-play path (DNP'd in v1):** USB-Ethernet controller on port B's hub
  (inbox drivers on all OSes) ↔ magnetics-less PHY-to-PHY link ↔ soft MAC +
  lwIP on Sapphire. Populate when driverless operation is wanted.
- Rejected: single-connector USB 3.0 hub design (port split is simpler and
  solves programming too); EZ-USB FX3 composite device (single-chip but puts the
  critical streaming path behind custom firmware).

## Control plane

Sapphire RISC-V SoC owns: TX/RX scheduling, LMX2582 SPI config, RF switch control (LNA/PA SPDT), AGC, calibration, PD/housekeeping, host control endpoint.

**Full-duplex rule:** the datapath (both DSP chains, both converter interfaces, both stream paths) is built simultaneous-capable from day one. TDD (the 10% duty cycle regime) is purely a *scheduler policy* in the SoC that gates the PA/LNA switches and TX enable. Future FDD = policy change + new RF filtering; no fabric redesign.

## DSP pipeline (parameters TBD in HDL phase)

```
RX: ADS4222 DDR-LVDS capture → DC/IQ correction → CIC + halfband decimation
    → sync (Schmidl-Cox class) + CFO (CORDIC) → FFT → per-carrier EQ
    → demap → FEC decode → deframe → host
TX: host → frame → FEC encode → map → IFFT → CP insert
    → halfband + CIC interpolation → I/Q/DC correction → AD9117
```

Sizing estimate: whole modem ~20–40k LUTs, ~20–40 DSP blocks — Tz170 is deliberately oversized (future-proofing + SoC + integration headroom). The HDL phase measures real utilization; part choice is revisited only if off by a lot.

## PCB & EMI

- ~8 layers, via-in-pad. Stackup **TBD**.
- AD9117 CMOS bus: buried stripline between two ground planes, via stitching fence at board edge, series termination at the FPGA drivers, minimum drive strength / slowest workable edge rate, lowest workable interface voltage. Required because FDD-future removes the "DAC quiet during RX" assumption.
- ADS4222 in DDR LVDS output mode (RX is the sensitive path).

## Expansion (mezzanine)

Spare HSIO routed to Samtec QSE-class connectors for future 2×2/4×4 MIMO converter daughtercards. The connector must carry: N spare LVDS pairs, the **shared 25 MHz sample clock**, a sync/trigger line, SPI/GPIO, and power — coherence is the point, not just pins. Differential 100 Ω, pair-internal matching only.

## Verification

- cocotb + cocotbext-axi; vendor-neutral RTL wherever possible (Efinity-specific only at hard-block boundaries: LPDDR4, PLLs, I/O).
- Sub-block testbenches + whole-system tests with simulated RF impairments (per `system_spec.md`).
- Utilization checkpoint after modem HDL exists → confirms/downsizes FPGA choice.

## Open items

1. JLC library stock check: ADS4222IRGCT, AD9117, FT601Q-B, FT4232H, PD sink, FF/fanout MPNs, LPDDR4, USB2 hub, USB-Ethernet + PHY.
2. OFDM numerology (FFT size, CP, subcarrier spacing, pilots) and FEC choice.
3. FT601 channel/framing protocol and host-side software stack (D3XX).
4. LPDDR4 part + density; whether Linux-on-Sapphire is wanted or bare-metal suffices.
5. Adapter/clock-board power source (carried over from LO-board work).
6. Stackup + converter analog front-end details (anti-alias filters for fixed 25 MSPS).
