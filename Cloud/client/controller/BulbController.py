import paho.mqtt.client as mqtt
import json
import time
import logging
from typing import Optional, Dict, Any

class BulbController:
    """
    MQTT灯泡控制器 (使用 paho-mqtt VERSION2 API)
    """

    def __init__(self, bulb_id: str, broker: str = "test.mosquitto.org", port: int = 1883):
        self.bulb_id = bulb_id
        self.broker = broker
        self.port = port
        self.current_state = None
        self.subscribed_topics = {}

        # 设置日志
        self.logger = logging.getLogger(f"Controller_{bulb_id}")
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # 使用新版API初始化MQTT客户端
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,  # 关键修改
            client_id=f"ctrl_{bulb_id}_{int(time.time())}",  # 唯一客户端ID
            protocol=mqtt.MQTTv5  # 使用MQTT 5.0协议
        )

        # 设置新版回调方法
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        # 基础主题
        self.base_topic = f"home/lights/{bulb_id}"

    def connect(self) -> bool:
        """连接MQTT代理"""
        try:
            self.client.connect(
                self.broker,
                self.port,
                keepalive=60
            )
            self.client.loop_start()
            self.logger.info("Connecting to MQTT broker...")
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
        """MQTT连接回调 (VERSION2签名)"""
        if reason_code.is_failure:
            self.logger.error(f"Connection failed with reason code: {reason_code}")
            return

        self.logger.info("Successfully connected to MQTT broker")

        # 订阅灯泡状态主题
        state_topic = f"{self.base_topic}/state"
        result, mid = client.subscribe(state_topic, qos=1)
        if result != mqtt.MQTT_ERR_SUCCESS:
            self.logger.error(f"Failed to subscribe to {state_topic}")
        else:
            self.logger.info(f"Subscribed to {state_topic}")

        # 请求初始状态
        self.get_state()

    def _on_message(self, client, userdata, message):
        """MQTT消息回调 (VERSION2兼容)"""
        try:
            topic = message.topic
            payload = message.payload.decode('utf-8')

            if topic.endswith("/state"):
                self.current_state = json.loads(payload)
                self.logger.debug(f"State updated: {self.current_state}")

                # 触发已注册的回调
                if topic in self.subscribed_topics:
                    self.subscribed_topics[topic](self.current_state)
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        """MQTT断开连接回调 (VERSION2)"""
        self.logger.warning(f"Disconnected with reason: {reason_code}")
        if reason_code != mqtt.MQTT_ERR_SUCCESS:
            self.logger.info("Attempting to reconnect...")
            self.connect()

    def turn_on(self) -> bool:
        """打开灯泡"""
        return self._send_command("set_state", {"state": "on"})

    def turn_off(self) -> bool:
        """关闭灯泡"""
        return self._send_command("set_state", {"state": "off"})

    def set_brightness(self, level: int) -> bool:
        """设置亮度 (0-100)"""
        if not 0 <= level <= 100:
            self.logger.error("Brightness must be between 0 and 100")
            return False
        return self._send_command("set_brightness", {"brightness": level})

    def set_color(self, color: str) -> bool:
        """设置颜色"""
        return self._send_command("set_color", {"color": color})

    def get_state(self) -> Optional[Dict]:
        """获取当前状态"""
        if self._send_command("get_state"):
            # 等待状态更新
            for _ in range(10):
                if self.current_state is not None:
                    return self.current_state
                time.sleep(0.1)
        return None

    def subscribe_state(self, callback) -> bool:
        """订阅状态更新"""
        state_topic = f"{self.base_topic}/state"
        self.subscribed_topics[state_topic] = callback
        return True

    def _send_command(self, command: str, payload: Optional[Dict] = None) -> bool:
        """发送MQTT命令"""
        topic = f"{self.base_topic}/control/{command}"

        try:
            result = self.client.publish(
                topic,
                payload=json.dumps(payload) if payload else "",
                qos=1,
                retain=False
            )

            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                self.logger.error(f"Failed to publish: {mqtt.error_string(result.rc)}")
                return False

            self.logger.debug(f"Command '{command}' sent to {topic}")
            return True
        except Exception as e:
            self.logger.error(f"Error sending command: {str(e)}")
            return False

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 创建控制器
    with BulbController("living_room_lamp") as controller:
        # 订阅状态更新
        def on_state_update(state):
            print(f"State update received: {state}")

        controller.subscribe_state(on_state_update)

        # 测试控制
        controller.turn_on()
        time.sleep(1)

        controller.set_brightness(75)
        time.sleep(1)

        controller.set_color("blue")
        time.sleep(1)

        print("Current state:", controller.get_state())

        controller.turn_off()
        time.sleep(1)