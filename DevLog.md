# DevLog: Troubleshooting Log

---

**Date:** 2026-01-21

## 1. Hardware Setup
- **Issue:** 초기 연결 시 전원 및 데이터 포트 혼동.
- **Solution:**
  - **Power:** Converter 2.0의 전원 포트(초록색 단자)에 12V 배터리(Cuktech) 연결. (팬 소음으로 전원 인가 확인)
  - **Data:** Converter 2.0의 이더넷 포트 -> USB-C 허브(UGREEN) -> 노트북 연결.
  - **Sync:** Handheld 구성이므로 Sync 케이블(파란/흰색 선)은 비연결 상태로 절연 처리.   



## 2. Network Configuration
#### 2.1 IP Connection Failure (Ping Unreachable)
- **Issue:** `192.168.1.50`으로 설정 후 Ping 시도 시 `Destination Host Unreachable` (100% Packet Loss) 발생.
- **Diagnosis:**
  - `tcpdump`로 패킷 분석 결과, 라이다가 기본 IP(`1.x` 대역)가 아닌 **`192.168.20.103`**으로 설정되어 있음을 발견 (이전 사용자가 변경함).
- **Solution:**
  - 노트북 Wired Settings 변경:
    - **IPv4 Method:** Manual
    - **Address:** `192.168.20.50` (라이다와 같은 20번 대역)
    - **Netmask:** `255.255.255.0`
    - **Gateway:** `0.0.0.0` (공란)
  - **Result:** `ping 192.168.20.103` 성공 (`time=1.59ms` 등 출력).

#### 2.2 Viewer Detection Failure
- **Issue:** Ping은 되지만 Livox Viewer 목록에 장비가 뜨지 않음.
- **Solution:**
  - **Wi-Fi OFF:** 무선 네트워크 간섭 제거.
  - **Firewall OFF:** `sudo ufw disable`로 방화벽 해제.
  - 방송 신호를 줍는 기능이 약해서인지 여전히 뜨지 않음. Viewer 대신 ROS 2 Rviz로 직접 확인하기로 결정



## 3. Software Setup (ROS 2 Driver)
#### 3.1 Driver Selection (Driver Version Mismatch)
- **Issue:** Horizon 모델에 맞지 않는 `livox_ros_driver2` (Humble branch) 설치 시도 -> 폴더 생성 안 됨.
- **Solution:** **`livox_ros2_driver`** (Livox SDK v1 기반)가 Horizon용 정석 드라이버임을 확인하고 설치.
  - `git clone https://github.com/Livox-SDK/livox_ros2_driver.git`

#### 3.2 'ament_cmake' not found
- **Issue**: ROS 2 환경변수 미로드.
- **Solution:** `source /opt/ros/humble/setup.bash`

#### 3.3 'shared_ptr' error in SDK
- **Issue:** 최신 Ubuntu 환경(GCC 11 이상)에서 Livox SDK 빌드 시 `<thread>` 관련 헤더 누락으로 컴파일 에러 발생.
- **Solution:** `Livox-SDK/sdk_core/src/base/thread_base.h` 파일에 `#include <memory>` 추가.
```bash
    sed -i '29i #include <memory>' Livox-SDK/sdk_core/src/base/thread_base.h
```

#### 3.4 'recompile with -fPIC' (Linker Error)
- **Issue**: SDK 빌드 시 공유 라이브러리 옵션 꺼짐.
- **Solution:** SDK 재빌드 (`cmake .. -DCMAKE_POSITION_INDEPENDENT_CODE=ON` 옵션 추가).



## 4 'Not in the whitelist' Error (Rviz)
- **Issue:** 드라이버 실행 시 연결 거부 메시지 출력.
- **Diagnosis:**
  - `config/livox_lidar_config.json` 설정 오류.
  - Horizon 모델은 **Broadcast Code(시리얼 넘버)** 끝에 숫자 `1`을 추가해야 함.
  - 입력한 시리얼 넘버에 오타 존재 (알파벳 `O` vs 숫자 `0`).
- **Solution:**
  - `broadcast_code` 수정: `"3WEDJBV001X652"` -> **`"3WEDJBV001X6521"`** (끝에 1 추가)
  - `enable_connect`: `true`로 변경.

---

**Date:** 2026-01-26

## 1. IMU Integration (WitMotion WT901C)
#### 1.1 Driver Availability Issue (Repository 404)
- **Issue:** `witmotion_ros2` 및 `EAVISE` 등 주요 오픈소스 드라이버의 GitHub 저장소가 삭제됨(404 Not Found).
- **Solution:** Custom Python Driver 개발.
  - `pyserial` 라이브러리를 이용해 `/dev/ttyUSB0`의 Raw Hex 데이터를 직접 파싱하고, ROS 2 sensor_msgs/Imu 타입의 /imu/data 토픽으로 발행하는 노드(`driver.py`)를 직접 구현하여 해결.

#### 1.2 Hardware Configuration (Ubuntu-based Fix)
- **Issue:** 드라이버 연결은 성공(`Connected`)했으나, 데이터가 `0000...` (Null)으로 들어오거나 침묵하는 현상 발생.
- **Diagnosis:** 센서의 Baudrate(9600)와 코드 설정(115200) 불일치 및 데이터 출력 비활성화 상태.
- **Solution:** Python Script를 이용한 Hex Command 주입 (Windows 환경에서 직접 바꾸기도 가능).
  - 별도의 설정 스크립트(`fix_sensor.py`)를 작성하여 리눅스 환경에서 직접 Hex 명령어 전송.
  - **Unlock** -> **Baudrate 115200 변경** -> **Output Rate 50Hz 설정** -> **Save** 순서로 명령어를 순차 주입하여 센서 강제 세팅 성공.

#### 1.3 Hardware Connection Instability (Port Drifting)
- **Issue:** USB 케이블 재연결 시 포트가 `/dev/ttyUSB0`에서 `/dev/ttyUSB1`로 변경되어 `No such file` 에러 발생.
- **Diagnosis:** 리눅스 커널이 기존 포트 세션을 유지한 채 새 장치로 인식함.
- **Solution:**
  - 물리적 고정: 케이블 흔들림 방지.
  - 실행 전 확인: `ls /dev/ttyUSB*` 명령어로 포트 확인 후, 필요시 코드 내 `self.port` 파라미터 수정.
  
#### 1.4 ROS 2 Environment Conflict
- **Issue:** 드라이버는 정상 작동하는데 Rviz에서 데이터가 수신되지 않음.
- **Diagnosis:**
  - **Alias 문제:** `local_setup.bash`만 로드하여 기본 ROS 패키지 경로가 누락됨.
- **Solution:**
  - Alias 수정: `source install/setup.bash` (local 제외)로 통일.



## 2. Visualization (Rviz2)
#### 2.1 Static Visualization (Arrows Not Moving)
- **Issue:** 데이터는 들어오는데 Rviz 화면의 화살표(Axes)가 회전하지 않음.
- **Diagnosis:** 초기 드라이버 코드가 `Angular Velocity`(각속도)만 전송하고, Rviz가 회전을 표현하는 데 필수적인 **`Orientation (Quaternion)`** 데이터를 계산하지 않음.
- **Solution:** **Euler to Quaternion 변환 로직 추가.**
  - 센서의 각도 패킷(`0x53`)을 파싱하여 Roll, Pitch, Yaw를 구하고, 이를 Quaternion(x, y, z, w)으로 변환하는 수식을 `driver.py`에 추가하여 해결.

#### 2.2 Topic Discovery Delay
- **Issue:** `ros2 topic list`에는 뜨지만 Rviz `By topic` 목록에 `/imu/data`가 즉시 뜨지 않음.
- **Solution:** 목록 갱신을 기다리지 않고 Topic 입력란에 **/imu/data**를 **직접 타이핑(Manual Entry)**하여 강제 연결 성공.

> 서칭할 때, 정확한 모델명보단 제조사까지만 쓰고, 뒤에 툴을 붙이자.(witmotion wt901c x, witmotion ros2 o)
---

