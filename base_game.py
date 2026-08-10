from abc import ABC, abstractmethod

class BaseGame(ABC):
    def __init__(self, robot_controller):
        self.robot = robot_controller
        self.game_title = "Base Game"

    @abstractmethod
    def update(self, frame, user_gesture, key):
        """
        매 프레임마다 실행되는 게임 로직
        :param frame: OpenCV 이미지 프레임
        :param user_gesture: VisionDetector가 구한 인식 제스처
        :param key: 누른 키보드 입력 값
        :return: (수정된 frame, 게임 상태 메시지 문자열)
        """
        pass

    @abstractmethod
    def reset(self):
        """게임 변수 초기화"""
        pass