import paho.mqtt.client as mqtt
import json
import time
import logging
from typing import Optional, Dict, Any

class SmartBulb:
    """
    MQTT智能灯泡设备模拟器（使用最新的paho-mqtt API VERSION2）
    """

    def __init__(self, device_id: str, broker: str, port: int = 1883):
        self.device_id = device_id
        self.broker = broker
        self.port = port
        self.state = "off"  # "on" or "off"
        self.brightness = 0  # 0-100
        self.color = "white"  # RGB values or color names

        # 设置日志
        self.logger = logging.getLogger(f"Bulb_{device_id}")
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # 使用新版MQTT API (VERSION2)
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,  # 明确使用VERSION2
            client_id=device_id
        )
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        # 基础主题
        self.base_topic = f"home/lights/{device_id}"

    def connect(self) -> bool:
        """连接MQTT代理"""
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            self.logger.info(f"Bulb {self.device_id} connecting to MQTT broker...")
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {str(e)}")
            return False

    def disconnect(self) -> bool:
        """断开MQTT连接"""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.logger.info("Disconnected from MQTT broker")
            return True
        except Exception as e:
            self.logger.error(f"Disconnection failed: {str(e)}")
            return False

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """MQTT连接回调（新版API签名）"""
        if reason_code.is_failure:
            self.logger.error(f"Connection failed with reason code: {reason_code}")
            return

        self.logger.info("Successfully connected to MQTT broker")
        # 订阅控制主题
        control_topic = f"{self.base_topic}/control/+"
        self.client.subscribe(control_topic, qos=1)
        self.logger.info(f"Subscribed to {control_topic}")

        # 发布初始状态
        self._publish_state()

    def _on_message(self, client, userdata, msg):
        """MQTT消息回调"""
        try:
            topic_parts = msg.topic.split('/')
            command = topic_parts[-1]  # 最后一个部分是命令

            payload = {}
            if msg.payload:
                payload = json.loads(msg.payload.decode('utf-8'))

            self.logger.debug(f"Received command '{command}' with payload: {payload}")

            # 处理不同命令
            if command == "set_state":
                self._handle_set_state(payload)
            elif command == "set_brightness":
                self._handle_set_brightness(payload)
            elif command == "set_color":
                self._handle_set_color(payload)
            elif command == "get_state":
                self._publish_state()
            else:
                self.logger.warning(f"Unknown command: {command}")

        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")

    def _handle_set_state(self, payload: Dict[str, Any]):
        """处理设置状态命令"""
        new_state = payload.get("state", "").lower()
        if new_state in ["on", "off"]:
            self.state = new_state
            self.brightness = 100 if new_state == "on" else 0
            self.logger.info(f"Bulb state changed to {new_state}")
            self._publish_state()
        else:
            self.logger.warning(f"Invalid state value: {new_state}")

    def _handle_set_brightness(self, payload: Dict[str, Any]):
        """处理设置亮度命令"""
        if self.state != "on":
            self.logger.warning("Cannot set brightness when bulb is off")
            return

        brightness = payload.get("brightness", 0)
        try:
            brightness = int(brightness)
            if 0 <= brightness <= 100:
                self.brightness = brightness
                self.logger.info(f"Brightness set to {brightness}%")
                self._publish_state()
            else:
                self.logger.warning(f"Brightness out of range: {brightness}")
        except ValueError:
            self.logger.warning(f"Invalid brightness value: {brightness}")

    def _handle_set_color(self, payload: Dict[str, Any]):
        """处理设置颜色命令"""
        if self.state != "on":
            self.logger.warning("Cannot set color when bulb is off")
            return

        color = payload.get("color", "white")
        self.color = color
        self.logger.info(f"Color changed to {color}")
        self._publish_state()

    def _publish_state(self):
        """发布当前状态"""
        state = {
            "state": self.state,
            "brightness": self.brightness,
            "color": self.color,
            "timestamp": int(time.time())
        }

        topic = f"{self.base_topic}/state"
        self.client.publish(topic, json.dumps(state), qos=1, retain=True)
        self.logger.debug(f"Published state to {topic}: {state}")

    def run(self):
        """运行设备"""
        self.connect()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.disconnect()


if __name__ == "__main__":
    # 示例用法
    bulb = SmartBulb(
        device_id="living_room_lamp",
        broker="test.mosquitto.org"
    )
    bulb.run()