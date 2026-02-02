import serial
import time

port = '/dev/ttyUSB0'

# WitMotion 프로토콜 (매뉴얼 기준)
UNLOCK = b'\xFF\xAA\x69\x88\xB5'      # 잠금 해제
SET_BAUD_115200 = b'\xFF\xAA\x04\x06\x00' # 속도 115200으로 변경
SAVE = b'\xFF\xAA\x00\x00\x00'       # 저장

def force_change_speed():
    print("🚀 센서 속도 강제 변경 시작...")
    
    # 전략: 9600과 115200 두 곳 모두에 "115200으로 바꿔!"라고 외침
    for current_baud in [9600, 115200]:
        print(f"📡 현재 {current_baud}라고 가정하고 명령 전송 중...", end="")
        try:
            ser = serial.Serial(port, current_baud, timeout=0.5)
            
            # 1. 잠금 해제
            ser.write(UNLOCK)
            time.sleep(0.05) 
            
            # 2. 115200으로 변경 명령
            ser.write(SET_BAUD_115200)
            time.sleep(0.05)
            
            ser.close()
            print(" [완료]")
        except Exception as e:
            print(f" [실패: {e}]")
            
    print("⏳ 센서 재부팅 대기 (2초)...")
    time.sleep(2)
    
    # 확인 사살
    print("🔎 115200으로 접속 테스트...")
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        # 저장 명령 전송
        ser.write(UNLOCK)
        time.sleep(0.05)
        ser.write(SAVE)
        
        start = time.time()
        while time.time() - start < 3:
            if ser.in_waiting:
                data = ser.read(ser.in_waiting)
                hex_data = data.hex().upper()
                if "5551" in hex_data:
                    print(f"✅ 성공! 정상 데이터 수신 중: {hex_data[:20]}...")
                    return
                elif "0000" in hex_data:
                    print("⚠️ 여전히 0000입니다. 하드웨어 고장이나 선 문제일 수 있습니다.")
            time.sleep(0.1)
        print("❌ 데이터가 들어오지 않습니다.")
    except Exception as e:
        print(f"❌ 접속 에러: {e}")

if __name__ == "__main__":
    force_change_speed()
