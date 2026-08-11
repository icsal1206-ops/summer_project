import random
import time
from base_game import BaseGame


class CCCGame(BaseGame):
    def __init__(self, robot_controller):
        super().__init__("CCC Game")
        self.robot = robot_controller
        self.state = "READY"
        self.start_time = 0
        self.countdown_sec = 3
        self.robot_choice = None
        self.user_choice = None
        self.result_text = ""
        self.scores = {"user": 0, "robot": 0}

    def start(self):
        self.state = "COUNTDOWN"
        self.start_time = time.time()
        self.robot_choice = random.choice(["LEFT", "RIGHT"])
        self.robot.move_to_pose("READY")

    def reset(self):
        self.state = "READY"
        self.result_text = ""
        self.robot.move_to_pose("HOME")

    def update(self, frame, gesture, key):
        elapsed = time.time() - self.start_time
        status_text = ""  # UnboundLocalError 방지용 기본값 지정

        if self.state == "READY":
            status_text = f"Press 'S' to Start! | User: {self.scores['user']} Robot: {self.scores['robot']}"

        elif self.state == "COUNTDOWN":
            remaining = self.countdown_sec - int(elapsed)
            if remaining > 0:
                status_text = f"Cham... Cham... Cham! ({remaining})"
            else:
                self.state = "RESULT"
                self.user_choice = gesture if gesture in ["LEFT", "RIGHT"] else "CENTER"
                
                self.robot.move_to_pose(self.robot_choice)

                if self.user_choice == self.robot_choice:
                    self.result_text = f"HIT! Robot Wins! (User:{self.user_choice} vs Bot:{self.robot_choice})"
                    self.scores["robot"] += 1
                else:
                    self.result_text = f"SAFE! User Wins! (User:{self.user_choice} vs Bot:{self.robot_choice})"
                    self.scores["user"] += 1

                status_text = f"{self.result_text} | User: {self.scores['user']} Robot: {self.scores['robot']}"
                self.start_time = time.time()

        elif self.state == "RESULT":
            status_text = f"{self.result_text} | User: {self.scores['user']} Robot: {self.scores['robot']}"
            if elapsed > 3.0:
                self.state = "READY"

        return status_text