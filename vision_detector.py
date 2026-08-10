import cv2
import mediapipe as mp


class VisionDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )

    def process(self, frame):
        """카메라 프레임에서 손을 감지하고 가위/바위/보 형태 반환"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        gesture = "NONE"

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # 손가락 뼈대 그리기
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                gesture = self._classify_gesture(hand_landmarks)

        return frame, gesture

    def _classify_gesture(self, landmarks):
        """손가락 펴짐 상태로 제스처 판단"""
        lm = landmarks.landmark
        
        index_open = lm[8].y < lm[6].y
        middle_open = lm[12].y < lm[10].y
        ring_open = lm[16].y < lm[14].y
        pinky_open = lm[20].y < lm[18].y

        if not index_open and not middle_open and not ring_open and not pinky_open:
            return "ROCK"
        elif index_open and middle_open and ring_open and pinky_open:
            return "PAPER"
        elif index_open and middle_open and not ring_open and not pinky_open:
            return "SCISSORS"
        elif index_open and not middle_open and not ring_open and not pinky_open:
            return "POINT"
            
        return "UNKNOWN"