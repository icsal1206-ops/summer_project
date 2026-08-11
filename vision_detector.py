import cv2
import mediapipe as mp
from collections import deque


class VisionDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        # 손 감지
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # 얼굴 감지 (인식률 확보를 위해 신뢰도 0.5로 설정)
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # 고개 위치 이동 평균 필터 (5프레임)
        self.ratio_history = deque(maxlen=5)

    def process(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame.shape
        
        face_direction = "CENTER"
        hand_gesture = "NONE"

        # 1. 얼굴(고개 방향) 인식
        face_results = self.face_mesh.process(rgb_frame)
        if face_results.multi_face_landmarks:
            for face_landmarks in face_results.multi_face_landmarks:
                # 얼굴 윤곽선 표시 (인식되고 있는지 눈으로 확인 가능)
                self.mp_draw.draw_landmarks(
                    image=frame,
                    landmark_list=face_landmarks,
                    connections=self.mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style()
                )

                lm = face_landmarks.landmark
                # 코끝(1번), 왼쪽 눈(33번), 오른쪽 눈(263번)
                nose_x = lm[1].x
                left_eye_x = lm[33].x
                right_eye_x = lm[263].x

                eye_dist = right_eye_x - left_eye_x
                if eye_dist > 0:
                    # 눈 사이 거리 대비 코 위치 비율 계산
                    raw_ratio = (nose_x - left_eye_x) / eye_dist
                    self.ratio_history.append(raw_ratio)
                    smooth_ratio = sum(self.ratio_history) / len(self.ratio_history)

                    # 거울 모드 화면 기준 임계값
                    if smooth_ratio < 0.38:
                        face_direction = "LEFT"
                    elif smooth_ratio > 0.62:
                        face_direction = "RIGHT"
                    else:
                        face_direction = "CENTER"

                    # 실시간 비율 수치 표시
                    cv2.putText(frame, f"Ratio: {smooth_ratio:.2f} ({face_direction})", (w - 300, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # 2. 손 인식
        hand_results = self.hands.process(rgb_frame)
        if hand_results.multi_hand_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                hand_gesture = self._classify_hand_gesture(hand_landmarks)

        current_gesture = face_direction if face_direction in ["LEFT", "RIGHT"] else hand_gesture
        return frame, current_gesture

    def _classify_hand_gesture(self, landmarks):
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
        return "UNKNOWN"