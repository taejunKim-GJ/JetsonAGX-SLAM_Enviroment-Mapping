# 🗺️ Environment Mapping: Handheld Sensor System

**"Handheld Sensor Systems for Data Acquisition & Mapping"**

이 프로젝트는 **LiDAR, Stereo Camera, IMU**가 장착된 핸드헬드 장비를 통해 데이터를 수집하고, **LiDAR SLAM** 및 **Gaussian Splatting**을 수행하여 정밀한 환경 맵을 생성하는 것을 목표로 합니다.

* **Target:** KCI Paper Submission (July)
* **Key Tech:** Sensor Calibration, Depth Map Generation (FoundationStereo), LiDAR SLAM + Gaussian Splatting
* **OS:** Ubuntu 22.04 LTS (Jammy Jellyfish)
* **Middleware:** ROS 2 Humble Hawksbill

---

## 🛠️ 1. Hardware Architecture
시스템은 다음과 같이 구성됩니다.

| Component | Model | Status | Connection |
| :--- | :--- | :--- | :--- |
| **LiDAR** | Livox Horizon | ✅ Ready | Ethernet (Converter 2.0) |
| **IMU** | WitMotion WT901C | ✅ Ready | USB (Serial) |
| **Camera** | ZED X (Stereo) | ✅ Ready | ZED QUAD Capture Card |
| **PC** | Nvidia Jetson AGX | ✅ Ready | - |
| **Power** | CUKTECH P23 (25,000mAh) | ✅ Ready | 12V DC (PD Output) |

---

## 📥 2. Installation (통합 설치)

이 저장소에는 프로젝트 실행에 필요한 모든 드라이버와 수정된 SDK가 포함되어 있습니다. 별도의 드라이버 다운로드 없이 아래 순서대로 진행하세요.

### 2.1 Clone Repository
전체 프로젝트를 다운로드합니다.
```bash
cd workspace
git clone https://github.com/taejunKim-GJ/Enviroment-Mapping-Slam.git
```

### 2.2 Install Dependencies
**1. System Libraries:**
IMU 드라이버 구동을 위한 시스템 라이브러리를 설치합니다.
```bash
sudo apt update
sudo apt install libasio-dev
```

**2. Livox SDK (Included Version):**
저장소에 포함된 Livox SDK(GCC 11+ 호환 패치 적용됨)를 빌드하고 설치합니다.
```bash
# 포함된 SDK 폴더로 이동
cd dependencies/Livox-SDK/build

# 빌드 및 설치
cmake .. -DCMAKE_POSITION_INDEPENDENT_CODE=ON
make -j$(nproc)
sudo make install

# 다시 워크스페이스 루트로 복귀
cd ~/workspace
```

### 2.3 Build Workspace
모든 ROS 2 패키지를 한 번에 빌드합니다.
```bash
# ROS 의존성 자동 설치
sudo rosdep init
rosdep update
rosdep install --from-paths src --ignore-src -r -y

# 전체 패키지 빌드
colcon build --symlink-install
source install/setup.bash
```

---

## ⚙️ 3. Configuration (하드웨어 설정)

### 3.1 Network Setup (LiDAR)
라이다와의 통신을 위해 PC의 유선 IP를 고정합니다.

1.  **Settings** > **Network** > **Wired** > **IPv4** > **Manual** 설정.
2.  **입력 값:**
    * **Address:** `192.168.20.50` (라이다 IP 대역에 맞추고, 끝자리는 라이다 IP와 겹치지 않는 임의의 번호 사용)
    * **Netmask:** `255.255.255.0`
    * **Gateway:** `0.0.0.0`
3.  **검증:**
    ```bash
    ping 192.168.20.103  # 본인 라이다 IP 입력하여 응답 확인
    ```

### 3.2 Broadcast Code Setup
사용하는 라이다 기기를 지정해야 합니다.
* **파일 경로:** `src/livox_ros2_driver/livox_ros2_driver/config/livox_lidar_config.json`
* **수정:** `"broadcast_code"` 항목에 라이다 뒷면 QR코드 아래의 **시리얼 넘버(14자리 + 1자리)**를 입력하세요.

### 3.3 USB Permission (IMU)
IMU 센서의 시리얼 포트 권한을 허용합니다.
```bash
sudo chmod 777 /dev/ttyUSB0
```
*(만약 장치가 `/dev/ttyUSB0`가 아닐 경우, `src/witmotion_ros2/config/witmotion.yaml` 파일을 수정하세요)*

---

## 🚀 4. Execution

각 터미널에서 환경 변수를 로드(`source install/setup.bash`)한 후 실행하세요.

**Terminal 1: Sensor Drivers (LiDAR)**
```bash
# LiDAR Driver 실행
ros2 launch livox_ros2_driver livox_lidar_msg_launch.py
```

**Terminal 2: Sensor Drivers (IMU)**
```bash
# IMU Driver 실행
ros2 launch witmotion_ros2 witmotion.launch.py
```

**Terminal 3: SLAM (FAST-LIO2)**
```bash
# Mapping 시작
ros2 launch fast_lio mapping.launch.py
```

---

## 📅 5. Next Steps
* [ ] **Stereo Camera (ZED 2) Integration:** Depth Map 생성 및 연동.
* [ ] **Extrinsic Calibration:** LiDAR-Camera-IMU 간 좌표계 통일.
* [ ] **Data Recording:** `ros2 bag record`를 통한 주행 데이터 수집.
* [ ] **SLAM Algorithm:** FAST-LIO2 최적화 및 Gaussian Splatting 파이프라인 구축.

---

This project uses code from 
[Livox SDK](https://github.com/Livox-SDK/Livox-SDK.git)
[Livox ROS2 Driver](https://github.com/Livox-SDK/livox_ros2_driver.git)
[Witmotion ROS2 Driver](https://github.com/ioio2995/witmotion_ros2.git)
[FAST-LIO2 ROS2](https://github.com/Ericsii/FAST_LIO_ROS2.git).
