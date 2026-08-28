"""K=7 convolutional code (133, 171 octal) with puncturing and soft Viterbi.

Same code as 802.11a/g BCC. Encoder state = last 6 input bits; the register
window is [current_bit, prev1..prev6] with the current bit in bit position 6.

LLR convention throughout the model: llr > 0 means bit 0 is more likely
(llr = log P(b=0)/P(b=1) up to a positive scale). Punctured positions are
depunctured as llr = 0 (erasure).
"""
from __future__ import annotations

import numpy as np

K = 7
NSTATES = 64
G0 = 0o133  # 1 + D^2 + D^3 + D^5 + D^6
G1 = 0o171  # 1 + D + D^2 + D^3 + D^6
TAIL_BITS = K - 1

# Puncturing patterns over the (A0 B0 A1 B1 ...) serialized coded stream,
# 802.11a conventions. 1 = transmit, 0 = puncture.
PUNCTURE = {
    (1, 2): np.array([1, 1], dtype=bool),
    (2, 3): np.array([1, 1, 1, 0], dtype=bool),
    (3, 4): np.array([1, 1, 1, 0, 0, 1], dtype=bool),
    (5, 6): np.array([1, 1, 1, 0, 0, 1, 1, 0, 0, 1], dtype=bool),
}


def _parity(x: np.ndarray) -> np.ndarray:
    x = x & 0x7F
    x ^= x >> 4
    x ^= x >> 2
    x ^= x >> 1
    return x & 1


def _tables():
    ns = np.arange(NSTATES)
    b_in = (ns >> 5) & 1                    # input bit that led into state ns
    pred = np.stack([(ns << 1) & 63, ((ns << 1) & 63) | 1], axis=1)  # (64, 2)
    reg = (b_in[:, None] << 6) | pred       # full 7-bit window per transition
    out0 = _parity(reg & G0)
    out1 = _parity(reg & G1)
    # Branch metric signs: +1 if coded bit 0, -1 if coded bit 1.
    sign0 = 1.0 - 2.0 * out0
    sign1 = 1.0 - 2.0 * out1
    return b_in, pred, sign0, sign1


B_IN, PRED, SIGN0, SIGN1 = _tables()


def conv_encode(bits: np.ndarray) -> np.ndarray:
    """Encode (caller appends the 6 zero tail bits). Returns 2*len(bits) bits."""
    bits = np.asarray(bits, dtype=np.int64)
    out = np.empty(2 * len(bits), dtype=np.uint8)
    state = 0
    for i, b in enumerate(bits):
        reg = (int(b) << 6) | state
        out[2 * i] = _parity(np.int64(reg & G0))
        out[2 * i + 1] = _parity(np.int64(reg & G1))
        state = reg >> 1
    return out


def puncture(coded: np.ndarray, rate: tuple[int, int]) -> np.ndarray:
    pat = PUNCTURE[rate]
    mask = np.resize(pat, len(coded))
    return coded[mask]


def depuncture(llrs: np.ndarray, rate: tuple[int, int], n_coded: int) -> np.ndarray:
    pat = PUNCTURE[rate]
    mask = np.resize(pat, n_coded)
    out = np.zeros(n_coded, dtype=np.float64)
    out[mask] = llrs[: int(mask.sum())]
    return out


def n_punctured_bits(n_info: int, rate: tuple[int, int]) -> int:
    """Coded bits after puncturing for n_info input bits (incl. tail)."""
    n_coded = 2 * n_info
    pat = PUNCTURE[rate]
    mask = np.resize(pat, n_coded)
    return int(mask.sum())


def viterbi_decode(llrs: np.ndarray, n_bits: int, terminated: bool = True) -> np.ndarray:
    """Soft-decision Viterbi over depunctured llrs (length 2*n_bits).

    terminated=True assumes the encoder was flushed to state 0 (tail bits
    included in n_bits); the traceback then starts from state 0.
    """
    llrs = np.asarray(llrs, dtype=np.float64).reshape(n_bits, 2)
    pm = np.full(NSTATES, -1e18)
    pm[0] = 0.0
    decisions = np.empty((n_bits, NSTATES), dtype=np.uint8)
    for t in range(n_bits):
        bm = SIGN0 * llrs[t, 0] + SIGN1 * llrs[t, 1]  # (64, 2)
        cand = pm[PRED] + bm
        decisions[t] = np.argmax(cand, axis=1)
        pm = np.max(cand, axis=1)
    state = 0 if terminated else int(np.argmax(pm))
    bits = np.empty(n_bits, dtype=np.uint8)
    for t in range(n_bits - 1, -1, -1):
        bits[t] = B_IN[state]
        state = PRED[state, decisions[t, state]]
    return bits
