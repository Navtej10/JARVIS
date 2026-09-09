"""
tracking/hand_tracker.py

Thin wrapper around MediaPipe Hands. This is the ONLY file that should ever
import mediapipe directly -- every other module talks to hands through the
`HandFrame` / `Landmark` types defined here, so the tracker can be swapped
later (e.g. for a different SDK or AR-glasses-native tracking in V7) without
touching gesture or interaction code.

TODO(V1): implement `HandTracker.process()` using MediaPipe Hands.
TODO(V1): apply confidence thresholding (drop frames below min_detection_confidence).
TODO(V4): support two-hand tracking with stable left/right ID assignment.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import math
import logging
import time
import cv2
import mediapipe as mp
class Handedness(Enum):
    LEFT = "left"
    RIGHT = "right"


@dataclass
class Landmark:
    """A single hand landmark in normalized [0,1] image coordinates."""
    x: float
    y: float
    z: float = 0.0  # populated in V6 by depth_tracker, otherwise MediaPipe's relative z


@dataclass
class HandFrame:
    """All landmarks + metadata for one detected hand in one camera frame."""
    handedness: Handedness
    landmarks: list[Landmark]        # 21 MediaPipe landmarks, index 0 = wrist
    detection_confidence: float
    timestamp_ms: int

    @property
    def wrist(self) -> Landmark:
        return self.landmarks[0]

    @property
    def index_tip(self) -> Landmark:
        return self.landmarks[8]

    @property
    def thumb_tip(self) -> Landmark:
        return self.landmarks[4]


class HandTracker:
    """
    Wraps the camera capture + MediaPipe Hands pipeline.

    Usage:
        tracker = HandTracker(camera_index=0, max_hands=1)
        for frame in tracker.stream():
            ...
    """

    def __init__(self, camera_index: int = 0, max_hands: int = 1,
                 min_detection_confidence: float = 0.7,
                 min_tracking_confidence: float = 0.5):
        self.camera_index = camera_index
        self.max_hands = max_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self._cap = None
        self._mp_hands = None
        self._hands = None
        self.latest_frame = None

    def start(self) -> None:
        """Open the camera and initialize the MediaPipe Hands model."""
        self._cap = cv2.VideoCapture(self.camera_index)
        if not self._cap.isOpened():
            raise RuntimeError(f"Failed to open camera {self.camera_index}")
            
        self._mp_hands = mp.solutions.hands
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=self.max_hands,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        )

    def read(self) -> list[HandFrame]:
        """Read a single frame and return detected hands (usually 0 or 1 in V1)."""
        if self._cap is None or self._hands is None:
            raise RuntimeError("HandTracker is not started. Call start() first.")
            
        success, image = self._cap.read()
        if not success:
            return []
            
        # Store latest frame for debug visualization
        self.latest_frame = image.copy()
        
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = self._hands.process(image_rgb)
        
        timestamp_ms = int(time.time() * 1000)
        hand_frames = []
        
        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                score = handedness.classification[0].score
                if score < self.min_detection_confidence:
                    continue
                    
                label = handedness.classification[0].label
                h_enum = Handedness.LEFT if label.lower() == "left" else Handedness.RIGHT
                
                landmarks = [Landmark(x=lm.x, y=lm.y, z=lm.z) for lm in hand_landmarks.landmark]
                
                # Hallucination filter: discard hands with impossible aspect ratios
                span = math.dist((landmarks[0].x, landmarks[0].y, landmarks[0].z), 
                                 (landmarks[9].x, landmarks[9].y, landmarks[9].z))
                knuckle_row_width = math.dist((landmarks[5].x, landmarks[5].y, landmarks[5].z), 
                                              (landmarks[17].x, landmarks[17].y, landmarks[17].z))
                                              
                if knuckle_row_width == 0:
                    continue
                    
                aspect = span / knuckle_row_width
                if aspect > 6.0 or aspect < 0.5:
                    logger = logging.getLogger("stark.main")
                    logger.debug(f"Discarding hallucinated hand frame (aspect ratio {aspect:.2f})")
                    continue
                
                hand_frames.append(HandFrame(
                    handedness=h_enum,
                    landmarks=landmarks,
                    detection_confidence=score,
                    timestamp_ms=timestamp_ms
                ))
                
        return hand_frames

    def stream(self):
        """Generator yielding HandFrame lists forever until stop() is called."""
        self.start()
        try:
            while True:
                yield self.read()
        finally:
            self.stop()

    def stop(self) -> None:
        """Release the camera and MediaPipe resources."""
        if self._hands is not None:
            self._hands.close()
            self._hands = None
        if self._cap is not None:
            self._cap.release()
            self._cap = None
