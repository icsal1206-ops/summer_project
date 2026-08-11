import cv2
import rclpy
from vision_detector import VisionDetector
from robot_controller import RobotController

# 게임 모듈 불러오기
from games.rps_game import RPSGame
from games.ccc import CCCGame


def main():
    rclpy.init()

    # 1. 모듈 초기화
    robot = RobotController()
    detector = VisionDetector()

    # 2. 게임 목록 등록 (키보드 1, 2번으로 선택 가능)
    games = {
        '1': RPSGame(robot),
        '2': CCCGame(robot)
    }
    current_game = games['1']  # 기본 실행: 가위바위보

    # 카메라 설정 (MJPEG 코덱)
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("=== Multigame Loaded ===")
    print("Select Game : '1' - 가위바위보 | '2' - 참참참")
    print("Controls    : 's' - 시작    | 'r' - 리셋   | 'q' - 종료")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 좌우 반전
        frame = cv2.flip(frame, 1)

        key = cv2.waitKey(1) & 0xFF

        # --- 키 입력 처리 ---
        if key == ord('q'):
            break
        elif key == ord('1'):
            current_game = games['1']
            current_game.reset()
            print(">> [가위바위보] 게임 선택됨")
        elif key == ord('2'):
            current_game = games['2']
            current_game.reset()
            print(">> [참참참] 게임 선택됨")
        elif key == ord('s'):
            current_game.reset()
            current_game.start()
        elif key == ord('r'):
            current_game.reset()

        # 비전 처리 (손 감지)
        frame, gesture = detector.process(frame)

        # 게임 상태 업데이트
        status_text = current_game.update(frame, gesture, key)

        # UI 화면 표시 (현재 게임 이름 및 상태)
        cv2.putText(frame, f"<{current_game.game_title}>", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(frame, str(status_text), (10, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow("Robot Game Console", frame)

        # ROS2 통신 유지
        rclpy.spin_once(robot, timeout_sec=0.001)

    cap.release()
    cv2.destroyAllWindows()
    rclpy.shutdown()


if __name__ == "__main__":
    main()