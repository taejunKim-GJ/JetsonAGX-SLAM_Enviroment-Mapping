import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import serial
import struct
import math

class WitmotionDriver(Node):
    def __init__(self):
        super().__init__('witmotion_driver')
        self.port = '/dev/ttyUSB0'
        self.baud = 115200
        self.pub = self.create_publisher(Imu, '/imu/data', 10)
        
        # 데이터를 모아서 한 번에 보내기 위한 임시 저장소
        self.acc = [0.0, 0.0, 0.0]
        self.gyro = [0.0, 0.0, 0.0]
        self.angle = [0.0, 0.0, 0.0] # Roll, Pitch, Yaw
        
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0.05)
            self.get_logger().info(f"✅ IMU Connected: {self.port} at {self.baud}")
        except Exception as e:
            self.get_logger().error(f"❌ Connection Failed: {e}")
            exit()
            
        # 0.01초(100Hz)마다 읽기 시도
        self.timer = self.create_timer(0.01, self.read_data)

    def read_data(self):
        try:
            while self.ser.in_waiting >= 11: # 패킷 크기(11바이트) 이상일 때만
                # 헤더 0x55 찾기
                if self.ser.read(1) != b'\x55':
                    continue
                
                # 나머지 10바이트 읽기
                data = self.ser.read(10)
                type_byte = data[0] # 패킷 타입 (51, 52, 53)
                
                # 데이터 파싱
                if type_byte == 0x51: # 가속도
                    self.acc[0] = struct.unpack('<h', data[1:3])[0] / 32768.0 * 16 * 9.8
                    self.acc[1] = struct.unpack('<h', data[3:5])[0] / 32768.0 * 16 * 9.8
                    self.acc[2] = struct.unpack('<h', data[5:7])[0] / 32768.0 * 16 * 9.8
                    
                elif type_byte == 0x52: # 각속도
                    self.gyro[0] = struct.unpack('<h', data[1:3])[0] / 32768.0 * 2000 * (math.pi / 180.0)
                    self.gyro[1] = struct.unpack('<h', data[3:5])[0] / 32768.0 * 2000 * (math.pi / 180.0)
                    self.gyro[2] = struct.unpack('<h', data[5:7])[0] / 32768.0 * 2000 * (math.pi / 180.0)
                    
                elif type_byte == 0x53: # 각도 (Euler Angle) -> Quaternion 변환 필요!     # TODO
                    r = struct.unpack('<h', data[1:3])[0] / 32768.0 * 180.0		#
                    p = struct.unpack('<h', data[3:5])[0] / 32768.0 * 180.0		#
                    y = struct.unpack('<h', data[5:7])[0] / 32768.0 * 180.0		#
                    self.publish_imu(r, p, y) # 각도 데이터가 오면 발행!			#

        except Exception as e:
            self.get_logger().error(f"Read Error: {e}")

    def get_quaternion_from_euler(self, roll, pitch, yaw):
        """
        Euler angles to Quaternion converter
        roll, pitch, yaw are in degrees
        """
        # Degree to Radian
        roll = math.radians(roll)
        pitch = math.radians(pitch)
        yaw = math.radians(yaw)

        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)

        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy

        return x, y, z, w

    def publish_imu(self, r, p, y):
        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "imu_link"
        
        # 1. Orientation (Quaternion) - 이게 있어야 Rviz 축이 움직임!
        x, y, z, w = self.get_quaternion_from_euler(r, p, y)
        msg.orientation.x = x
        msg.orientation.y = y
        msg.orientation.z = z
        msg.orientation.w = w
        
        # 2. Angular Velocity
        msg.angular_velocity.x = self.gyro[0]
        msg.angular_velocity.y = self.gyro[1]
        msg.angular_velocity.z = self.gyro[2]
        
        # 3. Linear Acceleration
        msg.linear_acceleration.x = self.acc[0]
        msg.linear_acceleration.y = self.acc[1]
        msg.linear_acceleration.z = self.acc[2]
        
        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = WitmotionDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
