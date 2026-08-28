"""OFDM modulator / demodulator (floating-point golden model).

TX:  scramble -> conv encode -> puncture -> per-symbol interleave -> QAM map
     -> subcarrier assembly (pilots, DC null) -> IFFT -> CP -> preamble prepend
RX:  Schmidl&Cox detect (STF autocorr) -> coarse CFO -> LTF cross-corr fine
     timing -> fine CFO -> LS channel estimate -> per-carrier EQ -> pilot CPE
     -> weighted max-log LLR -> deinterleave -> depuncture -> Viterbi
     -> descramble
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import fec
from .params import HEADER_MCS, MCS_TABLE, Mcs, Numerology

# ---------------------------------------------------------------------------
# Constellations (802.11a Gray mappings, unit average energy)
# ---------------------------------------------------------------------------

_PAM = {
    1: (np.array([-1.0, 1.0]), 1.0),                                # per axis: BPSK-like
    2: (np.array([-3.0, -1.0, 3.0, 1.0]), np.sqrt(10.0)),           # 16-QAM axis, gray idx
    3: (np.array([-7.0, -5.0, -1.0, -3.0, 7.0, 5.0, 1.0, 3.0]), np.sqrt(42.0)),
}
# _PAM[b][0][i] is the level whose Gray label is the integer i (MSB first).


def _axis_levels(bits_per_axis: int):
    levels, norm = _PAM[bits_per_axis]
    return levels / (norm if bits_per_axis > 1 else np.sqrt(2.0)), norm


def qam_map(bits: np.ndarray, bpsc: int) -> np.ndarray:
    """Map bit groups to complex symbols. bpsc in {2, 4, 6}."""
    ba = bpsc // 2
    levels, _ = _axis_levels(ba)
    b = bits.reshape(-1, bpsc)
    weights = 1 << np.arange(ba - 1, -1, -1)
    i_idx = (b[:, :ba] * weights).sum(axis=1)
    q_idx = (b[:, ba:] * weights).sum(axis=1)
    return levels[i_idx] + 1j * levels[q_idx]


def qam_llr(sym: np.ndarray, bpsc: int, weight: np.ndarray) -> np.ndarray:
    """Max-log per-bit LLRs (llr > 0 => bit 0). weight = |H|^2 / sigma^2."""
    ba = bpsc // 2
    levels, _ = _axis_levels(ba)
    labels = np.arange(len(levels))
    out = np.empty((len(sym), bpsc))
    for axis, y in ((0, sym.real), (1, sym.imag)):
        d2 = (y[:, None] - levels[None, :]) ** 2  # (nsym, nlevels)
        for bit in range(ba):
            m = (labels >> (ba - 1 - bit)) & 1
            d0 = d2[:, m == 0].min(axis=1)
            d1 = d2[:, m == 1].min(axis=1)
            out[:, axis * ba + bit] = weight * (d1 - d0)
    return out.ravel()


# ---------------------------------------------------------------------------
# Scrambler / interleaver
# ---------------------------------------------------------------------------

SCRAMBLER_SEED = 0b1011101  # x^7 + x^4 + 1, fixed nonzero seed


def scramble(bits: np.ndarray, seed: int = SCRAMBLER_SEED) -> np.ndarray:
    state = seed
    out = np.empty_like(bits)
    for i, b in enumerate(bits):
        fb = ((state >> 6) ^ (state >> 3)) & 1
        state = ((state << 1) | fb) & 0x7F
        out[i] = b ^ fb
    return out


def _interleave_perm(ncbps: int) -> np.ndarray:
    ncols = 13 if ncbps % 13 == 0 else 14  # 52 or 56 data carriers
    nrows = ncbps // ncols
    assert nrows * ncols == ncbps
    return np.arange(ncbps).reshape(nrows, ncols).T.ravel()


def interleave(bits: np.ndarray, ncbps: int) -> np.ndarray:
    perm = _interleave_perm(ncbps)
    return bits.reshape(-1, ncbps)[:, perm].ravel()


def deinterleave(vals: np.ndarray, ncbps: int) -> np.ndarray:
    perm = _interleave_perm(ncbps)
    v = vals.reshape(-1, ncbps)
    out = np.empty_like(v)
    out[:, perm] = v
    return out.ravel()


# ---------------------------------------------------------------------------
# Pilots / preamble
# ---------------------------------------------------------------------------

def _prbs7(n: int, seed: int = 0x7F) -> np.ndarray:
    state = seed
    out = np.empty(n, dtype=np.int8)
    for i in range(n):
        fb = ((state >> 6) ^ (state >> 5)) & 1
        state = ((state << 1) | fb) & 0x7F
        out[i] = 1 - 2 * fb
    return out


PILOT_BASE = np.array([1.0, 1.0, 1.0, -1.0])  # on carriers (-21, -7, 7, 21)
_POLARITY = _prbs7(127)


def pilot_values(sym_idx: int) -> np.ndarray:
    return PILOT_BASE * _POLARITY[sym_idx % 127]


def _ltf_freq(num: Numerology, rng_seed: int = 0x1234) -> np.ndarray:
    """+/-1 BPSK training on every occupied carrier, fixed pseudo-random signs."""
    rng = np.random.default_rng(rng_seed)
    return 1.0 - 2.0 * rng.integers(0, 2, size=len(num.occupied_carriers))


def _stf_freq(num: Numerology) -> tuple[np.ndarray, np.ndarray]:
    """Every-4th-carrier QPSK -> time-periodic with period nfft/4 (32 samples)."""
    ks = np.array([k for k in range(-num.kmax, num.kmax + 1)
                   if k != 0 and k % 4 == 0])
    rng = np.random.default_rng(0x5717)
    vals = (1 - 2 * rng.integers(0, 2, len(ks))) + 1j * (1 - 2 * rng.integers(0, 2, len(ks)))
    return ks, vals / np.sqrt(2.0)


@dataclass
class Preamble:
    stf: np.ndarray  # 2*nfft samples: 8 periods of nfft/4
    ltf: np.ndarray  # nfft/4 CP + 2*nfft samples
    ltf_freq: np.ndarray  # training values on occupied carriers
    ltf_time_1rep: np.ndarray  # one clean nfft-sample LTF repetition

    @property
    def samples(self) -> np.ndarray:
        return np.concatenate([self.stf, self.ltf])


def make_preamble(num: Numerology) -> Preamble:
    n = num.nfft
    # STF
    ks, vals = _stf_freq(num)
    X = np.zeros(n, dtype=complex)
    X[num.bins(ks)] = vals
    stf_t = np.fft.ifft(X) * n / np.sqrt(len(ks))
    stf = np.tile(stf_t[: n // 4], 8)
    # LTF
    lf = _ltf_freq(num)
    X = np.zeros(n, dtype=complex)
    X[num.bins(num.occupied_carriers)] = lf
    ltf_t = np.fft.ifft(X) * num.ifft_scale
    ltf = np.concatenate([ltf_t[-n // 4:], ltf_t, ltf_t])
    return Preamble(stf, ltf, lf, ltf_t)


# ---------------------------------------------------------------------------
# Frame header (SIG): 1 OFDM symbol, QPSK r1/2, always
# ---------------------------------------------------------------------------
# n_data info bits = mcs(4) len_bytes(12) flags(8) crc8(8) reserved tail(6)

def crc8(bits: np.ndarray) -> np.ndarray:
    """CRC-8, poly 0x07, over a bit array (MSB first)."""
    reg = 0
    for b in bits:
        reg = ((reg << 1) | int(b)) & 0x1FF
        if reg & 0x100:
            reg ^= 0x107
    for _ in range(8):
        reg = (reg << 1) & 0x1FF
        if reg & 0x100:
            reg ^= 0x107
    return np.array([(reg >> (7 - i)) & 1 for i in range(8)], dtype=np.uint8)


def _int_to_bits(v: int, n: int) -> np.ndarray:
    return np.array([(v >> (n - 1 - i)) & 1 for i in range(n)], dtype=np.uint8)


def _bits_to_int(bits: np.ndarray) -> int:
    return int("".join(str(int(b)) for b in bits), 2)


def pack_header(mcs_idx: int, length_bytes: int, n_bits: int = 52) -> np.ndarray:
    body = np.concatenate([_int_to_bits(mcs_idx, 4),
                           _int_to_bits(length_bytes, 12),
                           np.zeros(8, dtype=np.uint8)])  # flags
    return np.concatenate([body, crc8(body),
                           np.zeros(n_bits - 32, dtype=np.uint8)])  # rsvd+tail


def unpack_header(bits: np.ndarray):
    body, rx_crc = bits[:24], bits[24:32]
    if not np.array_equal(crc8(body), rx_crc):
        return None
    return _bits_to_int(body[:4]), _bits_to_int(body[4:16])


# ---------------------------------------------------------------------------
# Transmitter
# ---------------------------------------------------------------------------

CRC32_LEN = 32


def crc32_bits(bits: np.ndarray) -> np.ndarray:
    import zlib
    nbytes = np.packbits(bits.astype(np.uint8))
    v = zlib.crc32(nbytes.tobytes()) & 0xFFFFFFFF
    return _int_to_bits(v, 32)


def raised_cosine_ramp(n: int) -> np.ndarray:
    return 0.5 * (1 - np.cos(np.pi * (np.arange(n) + 0.5) / n))


def band_edge_fir(num: Numerology, stop_offset_hz: float = 145e3,
                  atten_db: float = 50.0) -> np.ndarray:
    """Linear-phase TX band-edge filter (scipy.signal.remez).

    Passband covers the occupied carriers, stopband from stop_offset_hz out.
    Applied at the 500 kHz modem rate on I and Q; in the FPGA this is one
    small real-coefficient FIR (~50-60 taps, fits in 1-2 time-shared DSPs).
    """
    from scipy import signal
    pass_edge = (num.kmax + 0.6) * num.df
    ntaps = 59
    h = signal.remez(ntaps, [0, pass_edge, stop_offset_hz, num.fs / 2],
                     [1, 0], weight=[1, 10 ** (atten_db / 20) / 10],
                     fs=num.fs)
    return h


class Transmitter:
    """OFDM transmitter.

    window_len: WOLA raised-cosine crossfade (samples) between adjacent
        symbols. The crossfade occupies the first window_len samples of each
        CP, eroding the effective multipath guard by that much; symbol
        advance stays nfft+ncp.
    use_tx_filter: apply the band-edge FIR (recommended shaping; preserves
        the full CP, the RX equalizer absorbs its in-band response).
    frame_ramp: RC amplitude ramp at burst start/end (EN 300 220-2 transient
        power requirement — no hard keying). The ramp-down runs over a cyclic
        dummy tail appended after the last symbol.
    """

    def __init__(self, num: Numerology, window_len: int = 2,
                 use_tx_filter: bool = True, frame_ramp: int = 32):
        self.num = num
        self.preamble = make_preamble(num)
        self.window_len = window_len
        self.frame_ramp = frame_ramp
        self.fir = band_edge_fir(num) if use_tx_filter else None

    def _ofdm_symbol(self, data_syms: np.ndarray, sym_idx: int) -> np.ndarray:
        num = self.num
        X = np.zeros(num.nfft, dtype=complex)
        X[num.bins(num.data_carriers)] = data_syms
        X[num.bins(num.pilot_carriers)] = pilot_values(sym_idx)
        x = np.fft.ifft(X) * num.ifft_scale
        return np.concatenate([x[-num.ncp:], x])

    def _assemble(self, blocks: list[tuple[np.ndarray, int]]) -> np.ndarray:
        """Concatenate (block, cp_len) tuples with WOLA crossfade windowing.

        Each block gets a cyclic suffix of window_len samples (the cyclic
        continuation past its end, i.e. b[cp_len:cp_len+nw]) with an RC
        ramp-down; the next block's first window_len samples (the front of
        its CP) get the complementary ramp-up, so adjacent symbols crossfade
        (up+down = 1). Advance per block is its own length; the crossfade
        erodes the effective CP by window_len samples.
        """
        nw = self.window_len
        if nw == 0:
            out = np.concatenate([b for b, _ in blocks])
        else:
            ramp = raised_cosine_ramp(nw)
            total = sum(len(b) for b, _ in blocks)
            out = np.zeros(total + nw, dtype=complex)
            pos = 0
            for b, cp_len in blocks:
                ext = np.concatenate([b, b[cp_len:cp_len + nw]])
                ext[:nw] *= ramp
                ext[-nw:] *= ramp[::-1]
                out[pos:pos + len(ext)] += ext
                pos += len(b)
        # burst power ramp (transient limit): ramp up over the frame head,
        # ramp down over an appended cyclic dummy tail
        fr = self.frame_ramp
        if fr:
            out = np.concatenate([out, out[len(out) - self.num.nfft:
                                           len(out) - self.num.nfft + fr]])
            out[:fr] *= raised_cosine_ramp(fr)
            out[-fr:] *= raised_cosine_ramp(fr)[::-1]
        if self.fir is not None:
            out = np.convolve(out, self.fir)
        return out

    def _encode_symbols(self, info_bits: np.ndarray, mcs: Mcs, start_sym: int):
        """info_bits (tail included, symbol-aligned) -> OFDM symbol samples."""
        num = self.num
        coded = fec.conv_encode(info_bits)
        coded = fec.puncture(coded, (mcs.rate_num, mcs.rate_den))
        ncbps = num.n_data * mcs.bpsc
        assert len(coded) % ncbps == 0
        inter = interleave(coded, ncbps)
        syms = qam_map(inter, mcs.bpsc).reshape(-1, num.n_data)
        return [self._ofdm_symbol(row, start_sym + i) for i, row in enumerate(syms)]

    def build_frame(self, payload: bytes, mcs_idx: int, rng=None) -> np.ndarray:
        num = self.num
        mcs = MCS_TABLE[mcs_idx]
        hdr_mcs = MCS_TABLE[HEADER_MCS]
        rng = rng or np.random.default_rng(0)

        # SIG symbol
        sig_bits = pack_header(mcs_idx, len(payload), num.n_data)
        sig_syms = self._encode_symbols(sig_bits, hdr_mcs, 0)

        # Payload: bits + CRC32, scrambled, + tail, padded to whole symbols
        pbits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))
        pbits = np.concatenate([pbits, crc32_bits(pbits)])
        pbits = scramble(pbits)
        pbits = np.concatenate([pbits, np.zeros(fec.TAIL_BITS, dtype=np.uint8)])
        ndbps = int(num.n_data * mcs.bpsc * mcs.rate)
        nsym = int(np.ceil(len(pbits) / ndbps))
        pad = nsym * ndbps - len(pbits)
        pbits = np.concatenate([pbits, rng.integers(0, 2, pad).astype(np.uint8)])
        data_syms = self._encode_symbols(pbits, mcs, len(sig_syms))

        ncp = num.ncp
        return self._assemble([(self.preamble.stf, 0),
                               (self.preamble.ltf, num.nfft // 4),
                               *((s, ncp) for s in sig_syms),
                               *((s, ncp) for s in data_syms)])

    def n_payload_symbols(self, length_bytes: int, mcs: Mcs) -> int:
        nbits = 8 * length_bytes + CRC32_LEN + fec.TAIL_BITS
        ndbps = int(self.num.n_data * mcs.bpsc * mcs.rate)
        return int(np.ceil(nbits / ndbps))


# ---------------------------------------------------------------------------
# Receiver
# ---------------------------------------------------------------------------

@dataclass
class RxDebug:
    detected: bool = False
    coarse_cfo: float = 0.0
    fine_cfo: float = 0.0
    ltf_start: int = -1
    header_ok: bool = False
    mcs_idx: int = -1
    length: int = -1
    cpe: np.ndarray | None = None
    evm_db: float = np.nan


class Receiver:
    """Frame receiver. Returns (payload_bytes | None, RxDebug)."""

    DETECT_THRESHOLD = 0.5
    TIMING_BACKOFF = 2  # start FFT window this many samples into the CP

    def __init__(self, num: Numerology):
        self.num = num
        self.preamble = make_preamble(num)

    # -- sync ---------------------------------------------------------------
    def _detect(self, r: np.ndarray):
        n = self.num.nfft
        lag = n // 4  # 32
        w = 2 * lag
        prod = r[:-lag] * np.conj(r[lag:])
        e = np.abs(r[lag:]) ** 2
        kern = np.ones(w)
        P = np.convolve(prod, kern, mode="valid")
        R = np.convolve(e, kern, mode="valid") + 1e-30
        M = np.abs(P) / R
        above = np.flatnonzero(M > self.DETECT_THRESHOLD)
        if len(above) < w:
            return None, 0.0
        d = int(above[0])
        # average the autocorr phase over the plateau for a stable coarse CFO
        span = slice(d + lag, d + 5 * lag)
        cfo = -np.angle(np.sum(P[span])) / (2 * np.pi * lag) * self.num.fs
        return d, cfo

    def _fine_timing(self, r: np.ndarray, approx: int):
        n = self.num.nfft
        ref = self.preamble.ltf_time_1rep
        lo = max(approx - 60, 0)
        hi = min(approx + 60, len(r) - 2 * n - 1)
        if hi <= lo:
            return None
        best_d, best_m = None, -1.0
        for d in range(lo, hi):
            c1 = np.abs(np.vdot(ref, r[d:d + n]))
            c2 = np.abs(np.vdot(ref, r[d + n:d + 2 * n]))
            m = c1 + c2
            if m > best_m:
                best_m, best_d = m, d
        return best_d

    # -- main ---------------------------------------------------------------
    def receive(self, r: np.ndarray):
        num, n = self.num, self.num.nfft
        dbg = RxDebug()

        d, coarse_cfo = self._detect(r)
        if d is None:
            return None, dbg
        dbg.detected = True
        dbg.coarse_cfo = coarse_cfo
        t = np.arange(len(r))
        r = r * np.exp(-2j * np.pi * coarse_cfo * t / num.fs)

        # LTF nominally starts 2*nfft (STF) + nfft/4 (LTF CP) after STF start
        ltf1 = self._fine_timing(r, d + 2 * n + n // 4)
        if ltf1 is None:
            return None, dbg
        # fine CFO from the two LTF repetitions
        acc = np.vdot(r[ltf1:ltf1 + n], r[ltf1 + n:ltf1 + 2 * n])
        fine_cfo = np.angle(acc) / (2 * np.pi * n) * num.fs
        r = r * np.exp(-2j * np.pi * fine_cfo * t / num.fs)
        dbg.fine_cfo = coarse_cfo + fine_cfo
        dbg.ltf_start = ltf1

        # channel estimate (timing backoff absorbed into H, cancels in EQ)
        bo = self.TIMING_BACKOFF
        occ = num.bins(num.occupied_carriers)
        F1 = np.fft.fft(r[ltf1 - bo:ltf1 - bo + n])[occ]
        F2 = np.fft.fft(r[ltf1 + n - bo:ltf1 + 2 * n - bo])[occ]
        H = 0.5 * (F1 + F2) / (self.preamble.ltf_freq * num.ifft_scale)
        sigma2 = np.mean(np.abs(F1 - F2) ** 2) / 2 / num.ifft_scale**2 + 1e-12
        weight_all = np.abs(H) ** 2 / sigma2

        occ_list = list(num.occupied_carriers)
        didx = [occ_list.index(k) for k in num.data_carriers]
        pidx = [occ_list.index(k) for k in num.pilot_carriers]

        def demod_symbol(i: int):
            start = ltf1 + 2 * n + i * (n + num.ncp) + num.ncp - bo
            if start + n > len(r):
                return None
            Y = np.fft.fft(r[start:start + n])[occ] / num.ifft_scale
            Yeq = Y / H
            # CPE: SNR-weighted pilot average (pilot values are real +/-1)
            cpe = np.angle(np.sum(Yeq[pidx] * pilot_values(i) * weight_all[pidx]))
            Yeq = Yeq * np.exp(-1j * cpe)
            return Yeq[didx], cpe

        # SIG
        hdr_mcs = MCS_TABLE[HEADER_MCS]
        res = demod_symbol(0)
        if res is None:
            return None, dbg
        ncbps = num.n_data * hdr_mcs.bpsc
        llr = qam_llr(res[0], hdr_mcs.bpsc, np.asarray(weight_all)[didx])
        llr = deinterleave(llr, ncbps)
        llr = fec.depuncture(llr, (1, 2), 2 * num.n_data)
        sig_bits = fec.viterbi_decode(llr, num.n_data)
        hdr = unpack_header(sig_bits)
        if hdr is None:
            return None, dbg
        dbg.header_ok = True
        dbg.mcs_idx, dbg.length = hdr
        if dbg.mcs_idx >= len(MCS_TABLE):
            return None, dbg
        mcs = MCS_TABLE[dbg.mcs_idx]

        # payload
        ndbps = int(num.n_data * mcs.bpsc * mcs.rate)
        nbits = 8 * dbg.length + CRC32_LEN + fec.TAIL_BITS
        nsym = int(np.ceil(nbits / ndbps))
        llrs, cpes, evm_acc = [], [], []
        for i in range(1, 1 + nsym):
            res = demod_symbol(i)
            if res is None:
                return None, dbg
            yeq, cpe = res
            cpes.append(cpe)
            w = np.asarray(weight_all)[didx]
            llrs.append(deinterleave(qam_llr(yeq, mcs.bpsc, w), num.n_data * mcs.bpsc))
            hard = qam_map(
                (qam_llr(yeq, mcs.bpsc, np.ones(len(yeq))) < 0).astype(np.uint8),
                mcs.bpsc)
            evm_acc.append(np.mean(np.abs(yeq - hard) ** 2))
        dbg.cpe = np.array(cpes)
        dbg.evm_db = 10 * np.log10(np.mean(evm_acc) + 1e-30)

        llr = np.concatenate(llrs)
        n_info_padded = nsym * ndbps
        llr = fec.depuncture(llr, (mcs.rate_num, mcs.rate_den), 2 * n_info_padded)
        bits = fec.viterbi_decode(llr, n_info_padded, terminated=False)
        bits = bits[:nbits - fec.TAIL_BITS]
        bits = scramble(bits)  # descramble (self-inverse with same seed)
        pbits, rx_crc = bits[:-32], bits[-32:]
        if not np.array_equal(crc32_bits(pbits), rx_crc):
            return None, dbg
        return np.packbits(pbits).tobytes(), dbg
