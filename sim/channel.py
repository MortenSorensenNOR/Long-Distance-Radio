"""Impairment channel: AWGN, CFO, TDL multipath, phase noise, quantization.

SNR convention: `snr_db` is signal power over noise power *in the occupied
bandwidth* (n_occupied * df ~ 219 kHz), matching how the link budget counts
noise in the 250 kHz channel (difference < 0.6 dB). Noise is generated white
over the full baseband fs with the PSD that yields that in-band SNR.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .params import Numerology


@dataclass
class ChannelConfig:
    snr_db: float = 100.0
    cfo_hz: float = 0.0
    # TDL multipath: exponential power-delay profile, Rayleigh taps
    # (tap 0 optionally Rician with k_factor_db), static over a frame.
    rms_delay_spread_s: float = 0.0
    max_excess_delay_s: float | None = None  # default: 5 * rms
    k_factor_db: float = 6.0  # Rician K on the first tap; -inf => Rayleigh
    phase_noise_linewidth_hz: float = 0.0  # Wiener (Lorentzian) linewidth
    quantize_bits: int = 0  # 0 = off; 12 = ADC model
    quantize_backoff_db: float = 12.0  # rms below full scale
    pad_samples: int = 400  # noise-only samples before/after the frame
    seed: int = 1


def tdl_taps(cfg: ChannelConfig, fs: float, rng: np.random.Generator) -> np.ndarray:
    if cfg.rms_delay_spread_s <= 0:
        return np.array([1.0 + 0j])
    tmax = cfg.max_excess_delay_s or 5 * cfg.rms_delay_spread_s
    ntaps = max(int(np.ceil(tmax * fs)) + 1, 2)
    t = np.arange(ntaps) / fs
    p = np.exp(-t / cfg.rms_delay_spread_s)
    p /= p.sum()
    h = np.sqrt(p / 2) * (rng.standard_normal(ntaps) + 1j * rng.standard_normal(ntaps))
    if np.isfinite(cfg.k_factor_db):
        k = 10 ** (cfg.k_factor_db / 10)
        # first tap: fixed LOS-ish component + scattered part
        h[0] = np.sqrt(p[0]) * (np.sqrt(k / (k + 1))
                                + h[0] / np.sqrt(p[0]) * np.sqrt(1 / (k + 1)))
    h /= np.sqrt(np.sum(np.abs(h) ** 2))  # unit average... normalized realization
    return h


def apply(tx: np.ndarray, num: Numerology, cfg: ChannelConfig) -> np.ndarray:
    rng = np.random.default_rng(cfg.seed)
    x = np.concatenate([np.zeros(cfg.pad_samples, dtype=complex), tx,
                        np.zeros(cfg.pad_samples, dtype=complex)])

    # multipath
    h = tdl_taps(cfg, num.fs, rng)
    x = np.convolve(x, h)

    # CFO (+ implicit random channel phase from the taps)
    n = np.arange(len(x))
    if cfg.cfo_hz:
        x = x * np.exp(2j * np.pi * cfg.cfo_hz * n / num.fs)

    # phase noise: Wiener process, variance-per-sample = 2*pi*linewidth/fs
    if cfg.phase_noise_linewidth_hz > 0:
        dphi = rng.standard_normal(len(x)) * np.sqrt(
            2 * np.pi * cfg.phase_noise_linewidth_hz / num.fs)
        x = x * np.exp(1j * np.cumsum(dphi))

    # AWGN, referenced to occupied bandwidth
    b_occ = len(num.occupied_carriers) * num.df
    sig_p = 1.0  # TX is built with unit average symbol power
    n0 = sig_p / b_occ / 10 ** (cfg.snr_db / 10)  # W/Hz
    sigma2 = n0 * num.fs
    noise = np.sqrt(sigma2 / 2) * (rng.standard_normal(len(x))
                                   + 1j * rng.standard_normal(len(x)))
    x = x + noise

    # ADC quantization
    if cfg.quantize_bits:
        rms = np.sqrt(np.mean(np.abs(x) ** 2))
        fullscale = rms * 10 ** (cfg.quantize_backoff_db / 20)
        q = fullscale / (2 ** (cfg.quantize_bits - 1))
        xi = np.clip(np.round(x.real / q), -2 ** (cfg.quantize_bits - 1),
                     2 ** (cfg.quantize_bits - 1) - 1)
        xq = np.clip(np.round(x.imag / q), -2 ** (cfg.quantize_bits - 1),
                     2 ** (cfg.quantize_bits - 1) - 1)
        x = (xi + 1j * xq) * q

    return x
