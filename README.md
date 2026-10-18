# Jetson AGX 기반 멀티센서 3D 환경 맵핑

Jetson AGX Orin에서 LiDAR, IMU, Stereo Camera를 ROS 2로 통합하고,  
투명체와 저텍스처 환경에서 발생하는 3D 맵핑 한계를 Camera Depth로 보완하는 프로젝트입니다.

LiDAR 기반 SLAM으로 기본 3D Map과 Odometry를 생성하고,  
Camera에서 얻은 Depth Point Cloud를 전역 좌표계로 변환하여 LiDAR Map과 함께 사용합니다.

<br>

## 1. 개요

- **프로젝트 목표:** LiDAR가 충분한 Point를 생성하지 못하는 유리창 영역을 Camera Depth로 보완
- **개발 환경:** Ubuntu 22.04 / ROS 2 Humble
- **주요 기술:** FAST-LIVO2, MoGe-2, PCL, OpenCV
- **개발 언어:** C++, Python
- **개발 보드:** NVIDIA Jetson AGX Orin 64GB

유리창과 같은 투명 물체는 LiDAR 신호가 투과하거나 불안정하게 반사되어 실제 공간에 존재함에도 Point Cloud에서 비어 있는 영역으로 나타날 수 있습니다.

이에 따라 LiDAR Map을 기본 공간 구조로 사용하면서 Camera Depth를 추가하는 방향으로 시스템을 구성했습니다.

<br>

## 2. 시스템 아키텍처

### 하드웨어 / 통신 구조

<!-- 추후 시스템 아키텍처 이미지 삽입 -->
<!-- <img width="700" alt="Hardware Architecture" src="./docs/images/hardware_architecture.png" /> -->

| 구분 | 장비 | 통신 / 연결 | 역할 |
|---|---|---|---|
| Edge Computer | NVIDIA Jetson AGX Orin 64GB | Ethernet / MIPI CSI-2 | ROS 2, SLAM, Depth 처리 |
| LiDAR & IMU | Livox Horizon | Ethernet | 3D Point Cloud 및 IMU 데이터 |
| Stereo Camera | ZED X | GMSL2 | Stereo Image 취득 |
| Capture Board | Stereolabs ZED Link Quad | GMSL2 → MIPI CSI-2 | Camera와 Jetson 연결 |
| LiDAR Power | CUKTECH Battery | DC | LiDAR 전원 공급 |
| System Power | Powercraft Battery | DC | Jetson 및 Capture Board 전원 공급 |
| Power Circuit | DC-DC Regulator | DC | 입력 전압 조정 |

Camera와 LiDAR 사이의 시차를 줄이기 위해 두 센서를 가깝게 배치하고,  
좌표계 차이는 Pitch / Roll 변환을 적용해 보정했습니다.

<br>

### 소프트웨어 구조

| 구분 | 사용 기술 |
|---|---|
| OS | Ubuntu 22.04 |
| Middleware | ROS 2 Humble |
| SLAM | FAST-LIVO2 |
| Depth Estimation | MoGe-2 |
| Point Cloud | PCL |
| Image Processing | OpenCV |
| Language | C++, Python |

<br>

### 디렉토리 구조

```text
JetsonAGX-SLAM_Enviroment-Mapping/
├── dependencies/
│   └── Livox-SDK/
│
├── src/
│   ├── FAST-LIVO2-ROS2-MID360-Fisheye/
│   ├── livox_ros2_driver/
│   ├── zed-ros2-wrapper/
│   └── ...
│
├── docs/
│   ├── Capstone_Report.pdf
│   ├── RAIV-RML_Joint_Workshop.pdf
│   └── images/
│
└── README.md
```

<br>

## 3. 핵심 기능

### 1) 멀티센서 데이터 취득

LiDAR, IMU, Camera 데이터를 ROS 2 환경에서 수집합니다.

- LiDAR / IMU: SLAM 및 Odometry 계산
- Camera: RGB Image 및 Depth 생성
- ROS Bag: 동일 구간의 센서 데이터 저장 및 반복 실험

<br>

### 2) LiDAR 기반 3D Mapping

FAST-LIVO2를 이용하여 LiDAR와 IMU를 기반으로 6-DoF Odometry와 기본 3D Map을 생성합니다.

생성된 Odometry는 이후 Camera Depth Point Cloud를 Local Frame에서 Global Frame으로 변환할 때 기준으로 사용합니다.

<!-- 추후 FAST-LIVO2 Mapping 결과 이미지 삽입 -->

<br>

### 3) Camera Depth Integration

ROS Bag의 Camera Frame에서 MoGe-2를 이용해 Depth Point Cloud를 생성합니다.

생성된 Point Cloud는 다음 과정으로 LiDAR Map에 반영합니다.

1. Depth PCD의 Timestamp와 SLAM State 대응
2. Camera Local Frame에서 Global Frame으로 좌표 변환
3. 일정 거리 이상의 Depth Point 제거
4. LiDAR Voxel Plane과 차이가 큰 Point 제거
5. Voxel 단위 중복 Point 제거

관련 코드:

`src/FAST-LIVO2-ROS2-MID360-Fisheye/src/LIVMapper.cpp`

주요 설정:

```yaml
depth_integration:
  enable: true
  time_threshold: 0.1
  scale: 1.0
  consistency_threshold: 0.2
  filter_size: 0.01
```

Camera Depth를 그대로 합치는 대신 기존 LiDAR Map의 공간 구조를 기준으로 사용할 Point를 선별하는 방식입니다.

<!-- 추후 Depth Integration Pipeline 이미지 삽입 -->

<br>

## 4. 실험 및 결과

### 평가 기준

Depth Estimation 결과는 Depth Image 자체보다 최종 3D Point Cloud를 기준으로 비교했습니다.

- 저텍스처 벽과 바닥에서도 공간 구조가 유지되는가
- 유리창 영역에 Depth가 생성되는가
- 3D 변환 후 거리와 형태가 과도하게 왜곡되지 않는가

<br>

### Depth 모델 비교

| 방식 | 확인된 문제 | 판단 |
|---|---|---|
| Stereo Depth | 저텍스처 벽과 정면 유리에서 Depth 누락 | 제외 |
| Relative Depth | 3D 변환 후 거리 증가에 따른 형태 왜곡 | 제외 |
| MoGe-2 | 기존 방식보다 안정적인 3D 구조 생성 | 최종 적용 |

여러 모델의 성능 자체를 비교하기보다 실제 Mapping에 사용할 수 있는 Point Cloud를 생성하는지를 기준으로 판단했습니다.

<br>

### Mapping 결과

FAST-LIVO2만 사용했을 때 누락되던 투명 영역에 Camera Depth를 추가하여 기존보다 조밀한 Point Cloud를 생성할 수 있음을 확인했습니다.

<!-- Before / After Mapping 결과 이미지 삽입 -->

<br>

### 현재 한계

현재 구조에서도 두 가지 문제가 남아 있습니다.

- **유리 너머 Background Depth**

  Monocular Depth가 유리면 자체가 아니라 유리 너머의 물체를 Depth로 추정하는 경우가 있습니다.

- **Curved Glass**

  현재 LiDAR Voxel의 Plane 정보를 기준으로 Point를 판단하기 때문에 곡면 유리에서는 평면 가정과 충돌할 수 있습니다.

향후에는 유리 영역을 별도로 분리한 뒤 해당 영역의 Depth를 보정하는 방향을 검토하고 있습니다.

<br>

## 5. 트러블슈팅

프로젝트 진행 중 발생한 하드웨어 및 개발 환경 문제는  
재현 조건, 확인 과정, 원인, 해결 방법을 GitHub Issue에 별도로 기록하고 있습니다.

### LiDAR Network Connection

- 공식 문서의 IP 주소로 LiDAR 연결 실패
- Host Network Interface 확인
- `tcpdump`로 실제 LiDAR Packet 확인
- 변경된 IP 확인 후 동일 Subnet으로 설정하여 통신 복구

[LiDAR Network Troubleshooting Issue](https://github.com/taejunKim-GJ/JetsonAGX-SLAM_Enviroment-Mapping/issues/1)

추가 Issue:

- Jetson AGX / ROS 2 개발 환경 구성
- ZED Link Quad JST Cable 극성 문제 및 통전 테스트

<br>

## 6. 시연 영상



<br>

## 7. 프로젝트 자료

### Capstone Report

[캡스톤 프로젝트 보고서](./docs/Capstone_Report.pdf)

Depth Estimation 모델 비교, 3D Point Cloud 실험 결과, 실패 사례 및 현재 한계를 정리한 보고서입니다.

### RAIV-RML Joint Workshop

[RAIV-RML Joint Workshop 발표자료](./docs/RAIV-RML_Joint_Workshop.pdf)

2026년 7월 RAIV-RML 연구실 교류회에서 발표한 자료로,  
시스템 구성과 FAST-LIVO2 + MoGe-2 기반 Mapping 결과를 정리했습니다.

<br>

## 8. 팀원 및 역할

| 팀원 | 담당 |
|---|---|
| 윤동식 | 3D Fusion 기반 기구 설계, 센서 배치 및 3D 프린팅 기반 하드웨어 제작 및 납땜, Calibration |
| 김태준 | Jetson 보드 젯팩 환경 구축, Depth Estimation, 라이다/카메라 연결 트러블슈팅 및 문서화 |
| 김찬효 | 센서 드라이버 및 SDK 구축, FAST-LIVO2 Mapping, Calibration, Depth Estimation AI 알고리즘 개발|

본 프로젝트는 각 담당 영역을 나눈 뒤 센서 데이터와 Mapping Pipeline을 최종 통합하는 방식으로 진행했습니다.

<br>

## Open Source

본 프로젝트는 다음 Open Source Project를 기반으로 진행했습니다.

- [Livox SDK](https://github.com/Livox-SDK/Livox-SDK.git)
- [Livox ROS2 Driver](https://github.com/Livox-SDK/livox_ros2_driver.git)
- ZED ROS 2 Wrapper
- FAST-LIVO2
- FAST-LIVO2 ROS 2 Humble Port
- MoGe-2
