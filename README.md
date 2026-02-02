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
| **Camera** | ZED 2 (Stereo) | 🚧 Pending | USB 3.0 |
| **PC** | Mini PC (NUC/Jetson) | ✅ Ready | - |
| **Power** | Portable Battery | ✅ Ready | 12V DC |

---

## 📡 2. Livox Horizon Setup (LiDAR)

### 2.1 Network Configuration (Wired)
라이다와의 통신을 위해 PC의 유선 IP를 고정합니다.

1.  **Settings** > **Network** > **Wired** > **IPv4** > **Manual** 설정.
2.  **입력 값:**
    * **Address:** `192.168.20.50`
    * **Netmask:** `255.255.255.0`
    * **Gateway:** `0.0.0.0`
3.  **검증:**
    ```bash
    ping 192.168.20.103
    # 64 bytes from ... (Success)
    ```

### 2.2 Dependencies (Livox SDK v1)
ROS 2 드라이버 구동을 위한 필수 SDK를 설치합니다. (GCC 11 호환 패치 적용)

```bash
# 1. Clone & Patch
cd ~
git clone https://github.com/Livox-SDK/Livox-SDK.git
sed -i '29i #include <memory>' Livox-SDK/sdk_core/src/base/thread_base.h

# 2. Build & Install (-fPIC 옵션 필수)
cd Livox-SDK/build
cmake .. -DCMAKE_POSITION_INDEPENDENT_CODE=ON
make -j$(nproc)
sudo make install
```

### 2.3 ROS 2 Driver Installation
Horizon 모델용 `livox_ros2_driver`를 빌드합니다.

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone https://github.com/Livox-SDK/livox_ros2_driver.git

cd ~/ros2_ws
colcon build --symlink-install --packages-select livox_ros2_driver
```

### 2.4 Configuration (Broadcast Code)
타겟 라이다를 지정하기 위해 Config 파일을 수정합니다.
* **Path:** `src/livox_ros2_driver/livox_ros2_driver/config/livox_lidar_config.json`
* **Mod:** `broadcast_code` 끝에 **숫자 `1`** 추가.

```json
{
  "lidar_config": [
    {
      "broadcast_code": "3WEDJBV001X6521",
      "enable_connect": true,
      "return_mode": 1,
      "coordinate": 0,
      "imu_rate": 1,
      "extrinsic_parameter_source": 0
    }
  ],
  "timesync_config": {
    "enable_timesync": false,
    "device_name": "/dev/ttyUSB0",
    "comm_device_type": 0,
    "baudrate_index": 2,
    "parity_index": 0
  }
}
```

---

## 🧭 3. WitMotion WT901C Setup (IMU)

### 3.1 USB Permission
USB 포트 권한을 확인하고 부여합니다.

```bash
ls /dev/ttyUSB*
# /dev/ttyUSB0 확인 (다를 경우 코드 수정 필요)
sudo chmod 777 /dev/ttyUSB0
```

### 3.2 Custom Driver Setup
공식 드라이버의 호환성 문제를 해결하기 위해 자체 제작한 Python 드라이버(`my_imu`)를 사용합니다.
* **Feature:** Raw Hex Parsing, 115200 Baudrate, Euler to Quaternion Conversion.
* 제공된 `my_imu` 폴더를 `~/ros2_ws/src/` 경로 안에 넣으세요.

```bash
# 워크스페이스 빌드 (IMU 패키지)
cd ~/ros2_ws
colcon build --symlink-install --packages-select my_imu
```

### 3.3 Visualization Tools
Rviz2 시각화를 위한 플러그인을 설치합니다.

```bash
sudo apt update
sudo apt install ros-humble-imu-tools
```

---

## 🚀 4. Execution & Visualization

### 4.1 Launch Sensors
두 개의 터미널을 열어 각각 실행합니다. 환경변수 로드(`source`)를 잊지 마세요.

**Terminal 1: LiDAR**
```bash
source ~/ros2_ws/install/setup.bash
ros2 launch livox_ros2_driver livox_lidar_rviz_launch.py
```

**Terminal 2: IMU**
```bash
source ~/ros2_ws/install/setup.bash
ros2 run my_imu driver
```
* *Check:* `✅ IMU Connected...` 로그가 출력되어야 합니다.

### 4.2 Rviz2 Verification
Rviz 화면에서 센서 데이터의 통합 및 동기화 상태를 시각적으로 검증합니다.

1.  **Run:** `rviz2`
2.  **Global Options:**
    * `Fixed Frame`: **livox_frame** (또는 TF Tree에 따라 `imu_link`)
3.  **Add Displays:**
    * **PointCloud2:** Topic `/livox/lidar`
    * **Imu:** Plugin `rviz_imu_plugin` → Topic `/imu/data`
4.  **Validation:**
    * 라이다 포인트 클라우드가 실시간으로 렌더링되는가?
    * 장비를 기울였을 때 IMU 화살표(Axes)가 물리적 움직임과 일치하게 회전하는가?

---

## 📅 5. Next Steps
* [ ] **Stereo Camera (ZED 2) Integration:** Depth Map 생성 및 연동.
* [ ] **Extrinsic Calibration:** LiDAR-Camera-IMU 간 좌표계 통일.
* [ ] **IMU Integration:** WitMotion IMU 드라이버 연동 및 시간 동기화(Time Sync) 테스트.
* [ ] **Data Recording:** `ros2 bag record`를 통한 주행 데이터 수집.
* [ ] **SLAM Algorithm:** FAST-LIO2 적용 테스트.
