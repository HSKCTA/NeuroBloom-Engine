"""
signal_generator.py
Generates synthetic EEG signals with physiological artifacts.
"""
import numpy as np
import random
from config import BASE_POWERS, BLINK_AMPLITUDE, JAW_CLENCH_NOISE

class EEGSimulator:
    def __init__(self):
        # State for Pink Noise generator (1/f filter state)
        self.noise_state = {band: 0.0 for band in BASE_POWERS.keys()}
        
    def _pink_noise(self, band_name):
        """Generates 1/f noise to make signals look biological."""
        white = random.uniform(-1, 1)
        # Simple IIR filter for pink noise approximation
        self.noise_state[band_name] = 0.95 * self.noise_state[band_name] + 0.05 * white
        return self.noise_state[band_name] * 1000

    def generate_epoch(self, state="NEUTRAL", behavior_modifiers=None):
        """
        Generates a 1-second snapshot of 8-band power.
        state: "FOCUSED", "DISTRACTED", "STRESSED", "DROWSY"
        behavior_modifiers: Dict of mouse/key metrics to modulate signal
        """
        powers = {}
        
        # 1. Base Generation with Pink Noise
        for band, base in BASE_POWERS.items():
            variance = base * 0.2  # 20% natural variance
            jitter = random.uniform(-variance, variance)
            powers[band] = base + jitter + self._pink_noise(band)

        # 2. State-Based Modulation (The Neuroscience Logic)
        if state == "FOCUSED":
            powers['low_beta'] *= 1.5   # Concentration
            powers['theta'] *= 0.6      # Suppression of wandering mind
            
        elif state == "DISTRACTED":
            powers['theta'] *= 1.8      # Daydreaming
            powers['delta'] *= 1.2
            powers['low_beta'] *= 0.7

        elif state == "STRESSED":
            powers['high_beta'] *= 2.0  # Anxiety
            powers['low_gamma'] *= 1.5  # Cognitive Overload
            powers['low_alpha'] *= 0.4  # Blocking of relaxation

        # 3. Behavioral Injection (The "Proxy" Logic)
        # Fast/Jerky mouse movements inject muscle noise (High Beta/Gamma artifacts)
        if behavior_modifiers:
            mouse_jerk = behavior_modifiers.get('mouse_jerk', 0)
            if mouse_jerk > 2.0:
                artifact = JAW_CLENCH_NOISE * (mouse_jerk / 5.0)
                powers['high_beta'] += artifact
                powers['low_gamma'] += artifact # EMG bleeds into Gamma

        # 4. Artifact Injection (Random Blinks)
        if random.random() < 0.05: # 5% chance of blink per epoch
            # Blinks mostly affect Delta/Theta
            powers['delta'] += BLINK_AMPLITUDE
            powers['theta'] += BLINK_AMPLITUDE / 2

        # Ensure no negative power
        return {k: max(0, v) for k, v in powers.items()}