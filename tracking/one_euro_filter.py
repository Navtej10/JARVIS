"""
One Euro Filter for smoothing noisy landmark coordinates in real time.

Reference: Casiez, Roussel, Vogel (2012) - "1€ Filter: A Simple Speed-based
Low-pass Filter for Noisy Input in Interactive Systems"

Usage pattern for this project:
- One OneEuroFilter instance per SCALAR value you want to smooth
  (e.g. one for cursor_x, one for cursor_y, or one per landmark axis)
- Call .filter(value, timestamp) every frame with the raw noisy value
- Use the returned value instead of the raw one downstream
"""

import math
import time


class OneEuroFilter:
    """
    Smooths a single scalar signal. Adaptive: heavier smoothing when the
    signal is nearly still (kills jitter), lighter smoothing when it moves
    fast (kills lag).

    Parameters
    ----------
    freq : float
        Expected sampling frequency in Hz (your camera FPS, e.g. 30).
        This is a fallback/default; if you pass real timestamps to
        .filter(), the instantaneous frequency is computed from them
        instead and this value barely matters.
    mincutoff : float
        Minimum cutoff frequency. LOWER = more smoothing at rest,
        but more lag when starting to move.
        Start at 1.0 and tune from there.
    beta : float
        Speed coefficient. HIGHER = more responsive during fast movement
        (less lag), but less smoothing during fast movement.
        Start at 0.0 (off) and increase gradually if you feel lag when
        moving the cursor quickly.
    dcutoff : float
        Cutoff frequency for filtering the derivative (speed) estimate
        itself. 1.0 is a sane default almost nobody needs to change.
    """

    def __init__(self, freq=30.0, mincutoff=1.0, beta=0.0, dcutoff=1.0):
        self.freq = freq
        self.mincutoff = mincutoff
        self.beta = beta
        self.dcutoff = dcutoff

        self.x_prev = None
        self.dx_prev = 0.0
        self.t_prev = None

    @staticmethod
    def _alpha(cutoff, te):
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / te)

    def filter(self, x, t=None):
        """
        x : raw noisy value (float)
        t : timestamp in seconds (e.g. time.time() or frame timestamp).
            If omitted, uses self.freq as a fixed-rate assumption.
        """
        if t is None:
            te = 1.0 / self.freq
        else:
            if self.t_prev is None:
                te = 1.0 / self.freq
            else:
                te = max(t - self.t_prev, 1e-6)  # avoid div-by-zero
            self.t_prev = t

        if self.x_prev is None:
            self.x_prev = x
            return x

        # Estimate speed of the signal, itself filtered to avoid noise
        # in the derivative dominating the cutoff calculation.
        dx = (x - self.x_prev) / te
        a_d = self._alpha(self.dcutoff, te)
        dx_hat = a_d * dx + (1 - a_d) * self.dx_prev

        # Adaptive cutoff: higher speed -> higher cutoff -> less lag.
        cutoff = self.mincutoff + self.beta * abs(dx_hat)
        a = self._alpha(cutoff, te)
        x_hat = a * x + (1 - a) * self.x_prev

        self.x_prev = x_hat
        self.dx_prev = dx_hat
        return x_hat

    def reset(self):
        """Call this when tracking is lost / hand re-enters frame, so the
        filter doesn't try to 'catch up' from a stale previous value."""
        self.x_prev = None
        self.dx_prev = 0.0
        self.t_prev = None


class LandmarkFilter:
    """
    Convenience wrapper: manages one OneEuroFilter per (landmark, axis)
    for a full 21-point MediaPipe hand, so you can filter the whole
    landmark array in one call instead of managing 21*2 filters by hand.

    filter_config lets you use DIFFERENT tuning for different purposes,
    e.g. lighter smoothing (more responsive) for the cursor-driving
    landmark, heavier smoothing (more stable) for landmarks feeding
    gesture classification (like pinch distance), since gesture
    classification cares about stability more than latency.
    """

    def __init__(self, num_landmarks=21, freq=30.0, mincutoff=1.0, beta=0.0, dcutoff=1.0):
        self.num_landmarks = num_landmarks
        self._filters = {
            (i, axis): OneEuroFilter(freq=freq, mincutoff=mincutoff, beta=beta, dcutoff=dcutoff)
            for i in range(num_landmarks)
            for axis in ("x", "y")
        }

    def filter(self, landmarks, t=None):
        """
        landmarks : list of 21 (x, y) tuples, normalized [0,1] coords
                    straight from MediaPipe HandLandmarker.
        t : timestamp in seconds. Pass real timestamps if you have them
            (e.g. from cv2 or the MediaPipe frame timestamp) for best
            results, especially if your frame rate varies.

        Returns: list of 21 (x, y) tuples, smoothed.
        """
        if t is None:
            t = time.time()

        smoothed = []
        for i, (x, y) in enumerate(landmarks):
            sx = self._filters[(i, "x")].filter(x, t)
            sy = self._filters[(i, "y")].filter(y, t)
            smoothed.append((sx, sy))
        return smoothed

    def reset(self):
        for f in self._filters.values():
            f.reset()
