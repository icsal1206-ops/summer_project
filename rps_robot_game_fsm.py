import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from cv_bridge import CvBridge

import cv2
import numpy as np
import random
import time
import subprocess
from enum import Enum

# MediaPipe 서브모듈 직접 불러오기 (Python 3.12 호환)
USE_MEDIAPIPE = False
try:
    import mediapipe.solutions.hands as mp_hands
    import mediapipe.solutions.drawing_utils as mp_draw
    USE_MEDIAPIPE = True
except Exception:
    USE_MEDIAPIPE = False

class GameState(Enum):
    IDLE = 0
    COUNTDOWN = 1
    DETECT = 2
    DECISION = 3
    ROBOT_ACTION = 4
    VERIFY = 5
    CEREMONY = 6
    COMPLETE = 7

class RockPaperScissorsFSMNode(Node):
    def __init__(self):
        super().__init__('rps_robot_game_fsm')

        # 1. ROS 2 토픽 발행자 설정
        self.joint_pub = self.create_publisher(JointTrajectory, '/arm_controller/joint_trajectory', 10)
        self.image_pub = self.create_publisher(Image, '/camera/image_raw', 10)
        self.bridge = CvBridge()

        # 2. 비전 엔진 초기화
        if USE_MEDIAPIPE:
            self.hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
            self.get_logger().info("비전 엔진: MediaPipe Hand Tracking 활성화")
        else:
            self.get_logger().info("비전 엔진: OpenCV Contour 손 감지 모드 활성화")

        # 3. 게임 상태 변수
        self.state = GameState.IDLE
        self.user_gesture = None
        self.robot_choice = None
        self.game_result = None
        self.countdown_start_time = None

        # 로봇 관절 위치 정의 [joint1, joint2, joint3, joint4] (rad)
        self.BOARD_POSES = {
            'ROCK': [0.5, 0.2, -0.2, -0.3],
            'SCISSORS': [0.0, 0.2, -0.2, -0.3],
            'PAPER': [-0.5, 0.2, -0.2, -0.3]
        }
        self.HOME_POSE = [0.0, 0.0, 0.0, 0.0]

        # 4. 웹캠 즉시 구동 (WSL2 초록 화면 예방)
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        for _ in range(10):
            self.cap.read()
            time.sleep(0.03)

        self.get_logger().info("★ 카메라 준비 완료! 화면을 클릭한 뒤 's' 키를 눌러 게임을 시작하세요.")
        self.timer = self.create_timer(0.033, self.process_frame)

    def classify_mediapipe(self, landmarks):
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        extended = [landmarks[tip].y < landmarks[pip].y for tip, pip in zip(tips, pips)]
        count = sum(extended)
        if count == 0: return 'ROCK'
        elif count == 2 and extended[0] and extended[1]: return 'SCISSORS'
        elif count >= 3: return 'PAPER'
        return 'UNKNOWN'

    def classify_opencv(self, frame):
        # MediaPipe 미지원 시 OpenCV 윤곽선 기반 감지
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            c = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(c)
            if area > 5000:
                hull = cv2.convexHull(c, returnPoints=False)
                defects = cv2.convexityDefects(c, hull)
                finger_count = 0
                if defects is not None:
                    for i in range(defects.shape[0]):
                        s, e, f, d = defects[i, 0]
                        if d > 10000:
                            finger_count += 1
                if finger_count == 0: return 'ROCK'
                elif finger_count == 1 or finger_count == 2: return 'SCISSORS'
                elif finger_count >= 3: return 'PAPER'
        return 'UNKNOWN'

    def publish_joint_pose(self, positions, duration_sec=1.5):
        msg = JointTrajectory()
        msg.joint_names = ['joint1', 'joint2', 'joint3', 'joint4']
        point = JointTrajectoryPoint()
        point.positions = positions
        point.time_from_start.sec = int(duration_sec)
        point.time_from_start.nanosec = int((duration_sec % 1) * 1e9)
        msg.points.append(point)
        self.joint_pub.publish(msg)

    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret or frame is None:
            return

        try:
            self.image_pub.publish(self.bridge.cv2_to_imgmsg(frame, encoding='bgr8'))
        except Exception:
            pass

        # FSM 상태 제어
        if self.state == GameState.IDLE:
            cv2.putText(frame, "PRESS 'S' TO START GAME", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)

        elif self.state == GameState.COUNTDOWN:
            elapsed = time.time() - self.countdown_start_time
            remaining = 3 - int(elapsed)
            if remaining > 0:
                cv2.putText(frame, f"COUNTDOWN: {remaining}", (180, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 2.5, (0, 0, 255), 5)
            else:
                self.state = GameState.DETECT

        elif self.state == GameState.DETECT:
            gesture = 'UNKNOWN'
            if USE_MEDIAPIPE:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(rgb_frame)
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                        gesture = self.classify_mediapipe(hand_landmarks.landmark)
            else:
                gesture = self.classify_opencv(frame)

            if gesture != 'UNKNOWN':
                self.user_gesture = gesture
                self.get_logger().info(f"[DETECT] 사용자 손모양 확정: {self.user_gesture}")
                self.state = GameState.DECISION
            else:
                cv2.putText(frame, "SHOW YOUR HAND!", (120, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)

        elif self.state == GameState.DECISION:
            options = ['ROCK', 'SCISSORS', 'PAPER']
            self.robot_choice = random.choice(options)

            if self.user_gesture == self.robot_choice:
                self.game_result = 'DRAW'
            elif (self.user_gesture == 'ROCK' and self.robot_choice == 'SCISSORS') or \
                 (self.user_gesture == 'SCISSORS' and self.robot_choice == 'PAPER') or \
                 (self.user_gesture == 'PAPER' and self.robot_choice == 'ROCK'):
                self.game_result = 'HUMAN_WIN'
            else:
                self.game_result = 'ROBOT_WIN'

            self.get_logger().info(f"[DECISION] 사람:{self.user_gesture} vs 로봇:{self.robot_choice} -> 결과:{self.game_result}")
            self.state = GameState.ROBOT_ACTION

        elif self.state == GameState.ROBOT_ACTION:
            self.publish_joint_pose(self.BOARD_POSES[self.robot_choice])
            time.sleep(1.5)
            self.state = GameState.VERIFY

        elif self.state == GameState.VERIFY:
            status_text = f"User: {self.user_gesture} | Robot: {self.robot_choice} -> {self.game_result}"
            cv2.putText(frame, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            if self.game_result == 'DRAW':
                self.get_logger().info("무승부! 재경기 진행!")
                self.publish_joint_pose([0.2, -0.1, 0.1, 0.0], duration_sec=1.0)
                time.sleep(1.0)
                self.countdown_start_time = time.time()
                self.state = GameState.COUNTDOWN
            else:
                self.state = GameState.CEREMONY

        elif self.state == GameState.CEREMONY:
            if self.game_result == 'HUMAN_WIN':
                self.get_logger().info("[CEREMONY] 사람 승리: 상품 전달 모션")
                self.publish_joint_pose([0.0, 0.4, -0.4, 0.0], duration_sec=1.0)
                time.sleep(2.0)
            else:
                self.get_logger().info("[CEREMONY] 로봇 승리: 댄스 세레머니")
                try:
                    subprocess.run(["python3", "play_recorded_dance.py"])
                except Exception:
                    pass

            self.state = GameState.COMPLETE

        elif self.state == GameState.COMPLETE:
            self.publish_joint_pose(self.HOME_POSE, duration_sec=2.0)
            self.get_logger().info("[COMPLETE] 초기 자세 복귀 완료.")
            self.state = GameState.IDLE

        cv2.imshow("RPS Robot Game GUI Dashboard", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s') and self.state == GameState.IDLE:
            self.countdown_start_time = time.time()
            self.state = GameState.COUNTDOWN

    def destroy_node(self):
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = RockPaperScissorsFSMNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        node.destroy_node()
        cv2.destroyAllWindows()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()