"""Locked PHY numerology and MCS definitions (candidate B, 56 occupied carriers).

Single source of truth for the golden model and, later, the cocotb reference.
See ofdm_investigation.md ("Session results") for the derivation.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

FS_CONVERTER = 25e6  # fixed converter rate, Hz
DECIMATION_R = 50  # 25 MHz / 50 = 500 kHz


@dataclass(frozen=True)
class Numerology:
    fs: float = FS_CONVERTER / DECIMATION_R  # 500 kHz baseband sample rate
    nfft: int = 128
    ncp: int = 8  # 8 samples = 16 us at 500 kHz (option: 4 = 8 us)
    # Occupied carriers: -28..-1, +1..+28 (DC nulled). 56 total.
    kmax: int = 28
    pilot_carriers: tuple = (-21, -7, 7, 21)
    null_dc_adjacent: bool = False  # option: also null k = +/-1 (zero-IF DC/1/f)

    @property
    def df(self) -> float:
        return self.fs / self.nfft  # 3906.25 Hz

    @property
    def t_useful(self) -> float:
        return self.nfft / self.fs  # 256 us

    @property
    def t_cp(self) -> float:
        return self.ncp / self.fs  # 16 us

    @property
    def t_symbol(self) -> float:
        return (self.nfft + self.ncp) / self.fs  # 272 us

    @property
    def occupied_carriers(self) -> np.ndarray:
        ks = [k for k in range(-self.kmax, self.kmax + 1) if k != 0]
        if self.null_dc_adjacent:
            ks = [k for k in ks if abs(k) != 1]
        return np.array(ks)

    @property
    def data_carriers(self) -> np.ndarray:
        return np.array(
            [k for k in self.occupied_carriers if k not in self.pilot_carriers]
        )

    @property
    def n_data(self) -> int:
        return len(self.data_carriers)  # 52

    @property
    def ifft_scale(self) -> float:
        # Makes E[|x[n]|^2] = 1 for unit-energy constellation points.
        return self.nfft / np.sqrt(len(self.occupied_carriers))

    def bins(self, carriers) -> np.ndarray:
        """Map signed carrier indices to numpy FFT bin indices."""
        return np.asarray(carriers) % self.nfft


@dataclass(frozen=True)
class Mcs:
    name: str
    bpsc: int  # coded bits per subcarrier (2 = QPSK, 4 = 16-QAM, 6 = 64-QAM)
    rate_num: int
    rate_den: int
    snr_ref_db: float  # approximate AWGN SNR (250 kHz ref BW) for BLER ~1e-2

    @property
    def rate(self) -> float:
        return self.rate_num / self.rate_den


# MCS ladder. snr_ref_db values are 802.11a-class planning numbers, verified
# against this model's own BLER curves by sim/run_ber.py.
MCS_TABLE = (
    Mcs("QPSK r1/2", 2, 1, 2, 5.0),    # MCS0 — also the SIG/header MCS
    Mcs("QPSK r3/4", 2, 3, 4, 8.0),    # MCS1
    Mcs("16QAM r1/2", 4, 1, 2, 10.5),  # MCS2
    Mcs("16QAM r3/4", 4, 3, 4, 14.0),  # MCS3
    Mcs("64QAM r2/3", 6, 2, 3, 18.0),  # MCS4
    Mcs("64QAM r3/4", 6, 3, 4, 20.0),  # MCS5
    Mcs("64QAM r5/6", 6, 5, 6, 22.0),  # MCS6 (extended)
)

HEADER_MCS = 0  # SIG symbol is always QPSK r1/2

NUM = Numerology()


def phy_rate(num: Numerology, mcs: Mcs) -> float:
    """Burst PHY rate in bit/s (data carriers only, pilots/CP excluded)."""
    return num.n_data * mcs.bpsc * mcs.rate / num.t_symbol
