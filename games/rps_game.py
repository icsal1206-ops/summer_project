import random
import time
import cv2
from base_game import BaseGame

class RPSGame(BaseGame):
    def __init__(self, robot_controller):
        super().__init__(robot_controller)
        self.game_title = "Rock Paper Scissors Game"
        
        self.state = "READY" # READY, COUNTDOWN, JUDGE, RESULT
        self.countdown_start = 0
        self.user_score = 0
        self.robot_score = 0
        self.result_text = "Press 'S' to Start!"
        self.robot_hand = None

    def reset(self):
        self.state = "READY"
        self.user_score = 0
        self.robot_score = 0
        self.result_text = "Game Reset. Press 'S' to Start!"
        self.robot.move_to_pose("READY")

    def update(self, frame, user_gesture, key):
        current_time = time.time()

        # 's' 키 누르면 시작
        if key == ord('s') and self.state == "READY":
            self.state = "COUNTDOWN"
            self.countdown_start = current_time
            self.robot.move_to_pose("READY")

        # 1. 카운트다운 진행 (3초)
        if self.state == "COUNTDOWN":
            elapsed = current_time - self.countdown_start
            count = 3 - int(elapsed)
            
            if count > 0:
                self.result_text = f"Get Ready... {count}"
            else:
                # 로봇 램덤 출제
                self.robot_hand = random.choice(["ROCK", "PAPER", "SCISSORS"])
                self.robot.move_to_pose(self.robot_hand, sec=0.5)
                self.state = "JUDGE"

        # 2. 승패 판정
        elif self.state == "JUDGE":
            if user_gesture in ["ROCK", "PAPER", "SCISSORS"]:
                winner = self._check_winner(user_gesture, self.robot_hand)
                if winner == "USER":
                    self.user_score += 1
                    self.result_text = f"You Win! (You:{user_gesture} vs Robot:{self.robot_hand})"
                elif winner == "ROBOT":
                    self.robot_score += 1
                    self.result_text = f"Robot Win! (You:{user_gesture} vs Robot:{self.robot_hand})"
                else:
                    self.result_text = f"Draw! (You:{user_gesture} vs Robot:{self.robot_hand})"
                
                self.state = "RESULT"
            else:
                self.result_text = "Show your hand clearly!"

        # 화면에 스코어 표시
        cv2.putText(frame, f"User: {self.user_score} | Robot: {self.robot_score}", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        return frame, self.result_text

    def _check_winner(self, user, robot):
        if user == robot:
            return "DRAW"
        if (user == "ROCK" and robot == "SCISSORS") or \
           (user == "PAPER" and robot == "ROCK") or \
           (user == "SCISSORS" and robot == "PAPER"):
            return "USER"
        return "ROBOT"