"""
config.py
Central configuration for NeuroBloom Simulation Framework.
"""

# EEG Frequency Bands (Hz) - Used for reference, though simulation works on Power directly
BANDS = {
    "delta": (0.5, 4),
    "theta": (4, 8),
    "low_alpha": (8, 10),
    "high_alpha": (10, 12),
    "low_beta": (12, 18),
    "high_beta": (18, 30),
    "low_gamma": (30, 40),
    "mid_gamma": (40, 50)
}

# Simulation Base Powers (uV^2/Hz) - Baselines for "Resting State"
BASE_POWERS = {
    "delta": 20000,
    "theta": 10000,
    "low_alpha": 15000,
    "high_alpha": 15000,
    "low_beta": 8000,
    "high_beta": 8000,
    "low_gamma": 3000,
    "mid_gamma": 2000
}

# Artifact Constants
BLINK_AMPLITUDE = 50000  # uV spike
JAW_CLENCH_NOISE = 15000 # Broad spectrum noise addition
SAMPLING_RATE = 256      # Hz