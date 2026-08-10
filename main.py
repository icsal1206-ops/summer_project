import cv2
import rclpy
from vision_detector import VisionDetector
from robot_controller import RobotController

# 게임 모듈 불러오기
from games.rps_game import RPSGame
# 나중에 새로운 게임 추가 시:
# from games.cham_cham_cham import ChamChamChamGame 

def main():
    rclpy.init()
    
    # 1. 모듈 초기화
    robot = RobotController()
    detector = VisionDetector()

    # 2. 플레이할 게임 선택 (추후 메뉴 형태로 선택 가능)
    current_game = RPSGame(robot)

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    print(f"=== {current_game.game_title} Loaded ===")
    print("Keys: 's' - Start | 'r' - Reset | 'q' - Quit")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1) # 좌우 반전
        
        # 3. 손 인식
        frame, gesture = detector.process(frame)

        # 4. 키 입력 받기
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            current_game.reset()

        # 5. 게임 로직 업데이트 및 화면 표시
        frame, status_text = current_game.update(frame, gesture, key)
        
        # 하단 메시지 출력
        cv2.putText(frame, status_text, (10, frame.shape[0] - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow(current_game.game_title, frame)

        # ROS2 통신 유지
        rclpy.spin_once(robot, timeout_sec=0.001)

    cap.release()
    cv2.destroyAllWindows()
    rclpy.shutdown()

if __name__ == '__main__':
    main()