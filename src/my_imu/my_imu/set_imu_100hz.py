import serial
import time
import struct

# ⚠️ 본인의 IMU 포트 이름으로 확인 후 수정 (예: /dev/ttyUSB0)
PORT = '/dev/ttyUSB0' 
# ⚠️ 본인의 IMU 통신 속도 (보통 115200 또는 9600)
BAUDRATE = 115200 

def set_100hz():
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=1)
        if ser.is_open:
            print(f"Connected to {PORT} at {BAUDRATE}")
            
            # 1. 잠금 해제 (Unlock)
            unlock_cmd = b'\xFF\xAA\x69\x88\xB5'
            ser.write(unlock_cmd)
            time.sleep(0.1)
            print("Unlock command sent.")

            # 2. 출력 속도 100Hz 설정 (Rate 100Hz = 0x09)
            # WitMotion 프로토콜: 0xFF 0xAA 0x03 [RATE] 0x00
            # RATE: 0x06(10Hz), 0x07(20Hz), 0x09(100Hz), 0x0B(200Hz)
            rate_cmd = b'\xFF\xAA\x03\x09\x00'
            ser.write(rate_cmd)
            time.sleep(0.1)
            print("Set 100Hz command sent.")

            # 3. 설정 저장 (Save)
            save_cmd = b'\xFF\xAA\x00\x00\x00'
            ser.write(save_cmd)
            time.sleep(0.1)
            print("Save command sent.")
            
            print("✅ 완료! 센서가 100Hz로 설정되었습니다.")
            ser.close()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("포트 권한이 없으면 'sudo chmod 777 /dev/ttyUSB0'를 먼저 실행하세요.")

if __name__ == '__main__':
    set_100hz()
