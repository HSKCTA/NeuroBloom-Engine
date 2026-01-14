"""
metrics_engine.py
Computes high-level cognitive metrics from fused sensor data.
"""
import numpy as np

class MetricsEngine:
    @staticmethod
    def compute_all(eeg_power, behavior_metrics, vision_metrics):
        """
        eeg_power: dict of 8 bands
        behavior_metrics: dict from BehavioralProcessor
        vision_metrics: dict (yaw, gaze, blink_count)
        """
        
        # --- 1. EEG DERIVATIVES ---
        theta = eeg_power['theta']
        beta = eeg_power['low_beta']
        alpha = eeg_power['low_alpha'] + eeg_power['high_alpha']
        gamma = eeg_power['low_gamma'] + eeg_power['mid_gamma']
        
        # Theta/Beta Ratio (ADHD Marker)
        # Range: 1.0 - 5.0 (Higher is worse)
        tbr = theta / beta if beta > 0 else 0

        # Cognitive Load Index (Dyscalculia Marker)
        # Gamma (Processing) vs Theta (Drift)
        cli = gamma / theta if theta > 0 else 0
        
        # Stress Index (Dyscalculia/Anxiety Marker)
        # High Beta (Anxiety) vs Alpha (Relaxation)
        stress_index = eeg_power['high_beta'] / alpha if alpha > 0 else 0

        # Engagement Score (General)
        # Beta / (Theta + Alpha) -> Ratio of Engagement vs Idleness
        engagement = beta / (theta + alpha) if (theta + alpha) > 0 else 0

        # Motor Fatigue (Dysgraphia Marker)
        # Simplistic: High Alpha during active task
        motor_fatigue = 0.0
        if behavior_metrics['velocity_avg'] > 1.0: # Active movement
            # If moving fast but Alpha is high, brain is fatiguing
            motor_fatigue = (alpha / 20000.0) 

        # --- 2. BEHAVIORAL DERIVATIVES ---
        
        # Hyperactivity Index (ADHD Marker)
        # High mouse jerk + high head velocity (simulated via vision yaw)
        head_instability = abs(vision_metrics.get('yaw_velocity', 0))
        hyperactivity = (behavior_metrics['jerk_avg'] * 10) + head_instability

        # Focus Ratio
        # Inverted Lookaway + Low Idle time
        lookaway_penalty = vision_metrics.get('gaze_deviation', 0) * 0.5
        idle_penalty = behavior_metrics['idle_ratio'] * 0.3
        focus_ratio = 1.0 - (lookaway_penalty + idle_penalty)
        focus_ratio = max(0.0, min(1.0, focus_ratio))

        # Writing Consistency (Dysgraphia Proxy)
        # High typing error rate + High flight time variance
        writing_inconsistency = (behavior_metrics['error_rate'] * 2) + \
                                (behavior_metrics['flight_time_var'] / 1000.0)

        # --- 3. RETURN STRUCTURE ---
        return {
            "engagement_score": round(engagement, 2),
            "motor_fatigue_rate": round(motor_fatigue, 2),
            "focus_ratio": round(focus_ratio, 2),
            "hyperactivity_index": round(hyperactivity, 2),
            "theta_beta_ratio": round(tbr, 2),
            "lookaway_frequency": round(vision_metrics.get('gaze_deviation', 0) * 10, 1), # Events/min
            "cognitive_load_index": round(cli, 2),
            "stress_index": round(stress_index, 2),
            "head_stability": round(100 - head_instability, 1),
            "writing_consistency_score": round(1.0 - min(1.0, writing_inconsistency), 2),
            "blink_variability": 0.5, # Placeholder for time-series calculation
            "distraction_time_sec": round((1.0 - focus_ratio) * 60, 1) # Per minute
        }