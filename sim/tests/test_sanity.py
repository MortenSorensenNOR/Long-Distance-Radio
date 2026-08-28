"""Sanity tests for the golden model. Run: uv run --with pytest pytest sim/tests"""
import numpy as np
import pytest

from sim import channel, fec
from sim.modem import (Receiver, Transmitter, deinterleave, interleave,
                       pack_header, qam_llr, qam_map, scramble, unpack_header)
from sim.params import MCS_TABLE, NUM


def _roundtrip(mcs_idx, cfg, payload_len=120, seed=3):
    tx, rx = Transmitter(NUM), Receiver(NUM)
    rng = np.random.default_rng(seed)
    payload = rng.integers(0, 256, payload_len, dtype=np.uint8).tobytes()
    wave = tx.build_frame(payload, mcs_idx, rng=rng)
    out, dbg = rx.receive(channel.apply(wave, NUM, cfg))
    return payload, out, dbg


# ---- unit level ----------------------------------------------------------

@pytest.mark.parametrize("rate", [(1, 2), (2, 3), (3, 4), (5, 6)])
def test_fec_roundtrip_noiseless(rate):
    rng = np.random.default_rng(0)
    n = 240 * rate[0] // 1  # multiple of pattern period
    bits = np.concatenate([rng.integers(0, 2, n, dtype=np.uint8),
                           np.zeros(6, dtype=np.uint8)])
    coded = fec.puncture(fec.conv_encode(bits), rate)
    llr = fec.depuncture(1.0 - 2.0 * coded.astype(float), rate, 2 * len(bits))
    dec = fec.viterbi_decode(llr, len(bits))
    assert np.array_equal(dec, bits)


@pytest.mark.parametrize("bpsc", [2, 4, 6])
def test_qam_map_llr_roundtrip(bpsc):
    rng = np.random.default_rng(1)
    bits = rng.integers(0, 2, 52 * bpsc, dtype=np.uint8)
    sym = qam_map(bits, bpsc)
    assert np.isclose(np.mean(np.abs(sym) ** 2), 1.0, atol=0.15)
    hard = (qam_llr(sym, bpsc, np.ones(len(sym))) < 0).astype(np.uint8)
    assert np.array_equal(hard, bits)


def test_interleaver_roundtrip():
    for bpsc in (2, 4, 6):
        ncbps = 52 * bpsc
        v = np.arange(3 * ncbps, dtype=float)
        assert np.array_equal(deinterleave(interleave(v, ncbps), ncbps), v)


def test_scrambler_self_inverse():
    rng = np.random.default_rng(2)
    b = rng.integers(0, 2, 999, dtype=np.uint8)
    assert np.array_equal(scramble(scramble(b)), b)


def test_header_roundtrip():
    bits = pack_header(5, 1500)
    assert len(bits) == 52
    assert unpack_header(bits) == (5, 1500)
    bad = bits.copy()
    bad[3] ^= 1
    assert unpack_header(bad) is None


# ---- end-to-end ----------------------------------------------------------

@pytest.mark.parametrize("mcs_idx", range(len(MCS_TABLE)))
def test_ideal_channel_all_mcs(mcs_idx):
    """TX -> near-ideal channel -> RX must be error-free at high SNR."""
    payload, out, dbg = _roundtrip(mcs_idx, channel.ChannelConfig(snr_db=45))
    assert dbg.detected and dbg.header_ok
    assert dbg.mcs_idx == mcs_idx and dbg.length == len(payload)
    assert out == payload


def test_worst_case_cfo():
    """Full +/-870 Hz TCXO offset (22% of subcarrier spacing)."""
    for cfo in (870.0, -870.0):
        payload, out, dbg = _roundtrip(
            5, channel.ChannelConfig(snr_db=35, cfo_hz=cfo))
        assert out == payload
        assert abs(dbg.fine_cfo - cfo) < 20.0  # Hz


def test_multipath_within_cp():
    """1 us rms delay spread (max excess 5 us < 16 us CP), several seeds."""
    ok = 0
    for seed in range(5):
        payload, out, dbg = _roundtrip(
            3, channel.ChannelConfig(snr_db=30, rms_delay_spread_s=1e-6,
                                     seed=100 + seed))
        ok += out == payload
    assert ok >= 4  # allow one deep-fade realization at 16-QAM r3/4


def test_combined_impairments_with_quantization():
    payload, out, dbg = _roundtrip(
        3, channel.ChannelConfig(snr_db=28, cfo_hz=870.0,
                                 rms_delay_spread_s=1e-6,
                                 phase_noise_linewidth_hz=50.0,
                                 quantize_bits=12, seed=7))
    assert out == payload


def test_low_snr_frame_fails_gracefully():
    payload, out, dbg = _roundtrip(5, channel.ChannelConfig(snr_db=5))
    assert out is None or out == payload  # never a corrupt "success"
