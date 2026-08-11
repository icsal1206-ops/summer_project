계획서
manipulator와 openCV, yolo를 활용한 로봇 팔과 대결하는 다양한 미니게임 만들기
ex)가위바위보, 참참참 등

1. 프로젝트 개요

주제: OpenCV와 YOLO 비전 인식을 활용하여 로봇 팔(OpenMANIPULATOR-X)과 사용자가 실시간으로 반응하며 즐기는 대화형 미니게임 플랫폼 (가위바위보, 참참참 등)

주요 목표:

YOLO/OpenCV를 통해 사용자의 손 모양(가위/바위/보) 및 참참참 방향(좌/우/중앙)을 실시간 검출

게임 상태 머신(Decision Node)을 구축하여 카운트다운, 승패 판정, 결과 동작 명령 처리

로봇 팔의 관절 제어(JointTrajectory / MoveIt Pose)를 통해 승패에 따른 액션(세레머니, 아쉬운 동작, 뿅망치 타격 등) 수행

주 검증 환경: [ ] Gazebo Harmonics / [ ] 실제 OpenMANIPULATOR-X (택 1)

2. 조원 및 역할

Vision 담당: (김동호, 이상진) - 카메라 입력 수신, YOLO/OpenCV 기반 사용자 손 동작 및 얼굴/시선 방향 인식 모델 구현

ROS 통합 담당: (김동호, 김병준) - Vision-Decision-Robot 노드 간 Topic/Action 인터페이스 설계, Launch 파일 작성 및 상태 머신 구성

Robot 담당: (김병준, 이상진) - OpenMANIPULATOR-X 관절 제어, 가위바위보 및 참참참 모션(Pose/Trajectory) 및 그리퍼 동작 구현

검증·문서 담당: (김동호) - 게임 규칙 시나리오 테스트, 에러 상태 검증, 시연 영상 편집, README 및 프로젝트 기술서 작성


3. 시스템 구성안

3.1 노드 및 데이터 흐름 (Node Graph)
USB Camera / Gazebo Camera
        ↓ (/camera/image_raw)
Vision Node (OpenCV / YOLO)
  ├─ 가위/바위/보 클래스 검출 (YOLO Detection/Segmentation)
  └─ 얼굴/손 이동 방향 검출 (HSV / Contour / YOLO)
        ↓ (/game/user_gesture, /game/detection_result)
Decision Node (Game State Machine)
  ├─ 게임 카운트다운 및 승패 판정 로직
  └─ 게임 진행 상태 및 스코어 관리
        ↓ (/robot/command_pose, FollowJointTrajectory Action)
Robot Control Node (OpenMANIPULATOR-X)
  ├─ 사전 정의된 미니게임 동작 (카운트다운 쉐이킹, 가위/바위/보 출력 Pose)
  └─ 승패 반응 액션 (승리 세레머니, 패배 동작, 그리퍼 제어)
        ↓
OpenCV Result Window / RViz2 / Console Log (실시간 점수 및 게임 상태 표시)

5. 미니게임 시나리오 및 상태 머신 (State Machine)
4.1 구현 게임 종류
가위바위보: 로봇이 카운트다운 동작 후 랜덤/인공지능으로 손 모양(Pose)을 제시하고, 카운트 시점의 사용자 손 모양(YOLO)을 인식하여 승패 판정 및 승리 세레머니 수행

참참참: 로봇이 지시봉/손끝을 특정 방향(좌/우)으로 가리킬 때, 사용자의 고개/손 방향을 인식하여 승/패 판단

5. 모니터링 및 상태 확인 방식
[x] OpenCV Result Window: 카메라 영상 위에 실시간 게임 상태(카운트다운, 승/패/무, 현재 스코어, YOLO Bounding Box) 표시

[x] Console Log / RQt: ROS 2 Node 상태 및 Action 진행 상황 출력

[x] RViz2: 로봇의 현재 관절 상태 및 TF2 좌표 모니터링



2026-08-10
오전
김동호: 프로젝트 주제 상의
이상진: 프로젝트 주제 상의
김병준: 프로젝트 주제 상의
이진호: 프로젝트 주제 상의



오후
김동호: 프로젝트 주제 상의
이상진: 프로젝트 코드 작성
김병준: 프로젝트 주제 상의
이진호: 프로젝트 주제 상의
