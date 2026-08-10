import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

class RobotController(Node):
    def __init__(self):
        super().__init__('robot_game_controller')
        self.publisher = self.create_publisher(
            JointTrajectory, 
            '/arm_controller/joint_trajectory', 
            10
        )
        self.joint_names = ['joint1', 'joint2', 'joint3', 'joint4']

        # 사전 정의된 로봇 포즈 (라디안 단위)
        self.POSES = {
            'HOME': [0.0, -1.0, 0.3, 0.7],
            'READY': [0.0, 0.0, 0.0, 0.0],
            'ROCK': [0.0, 0.5, -0.3, -0.2],
            'PAPER': [0.0, -0.5, 0.5, 0.0],
            'SCISSORS': [-0.3, -0.2, 0.2, 0.0],
            'LEFT': [0.8, -0.2, 0.2, 0.0],   # 참참참 확장용
            'RIGHT': [-0.8, -0.2, 0.2, 0.0], # 참참참 확장용
            'WIN': [0.0, -0.8, 0.8, -0.5],
            'LOSE': [0.0, 0.8, -0.5, 0.5]
        }

    def move_to_pose(self, pose_name, sec=1.0):
        """이름으로 로봇 자세 변경"""
        if pose_name not in self.POSES:
            self.get_logger().warn(f"Pose '{pose_name}' not defined!")
            return

        msg = JointTrajectory()
        msg.joint_names = self.joint_names

        point = JointTrajectoryPoint()
        point.positions = self.POSES[pose_name]
        point.time_from_start = Duration(sec=int(sec), nanosec=int((sec % 1) * 1e9))

        msg.points.append(point)
        self.publisher.publish(msg)
        self.get_logger().info(f"Robot action: {pose_name}")