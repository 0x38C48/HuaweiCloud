import paho.mqtt.client as mqtt
import json
import time
import logging
from typing import Dict, Any, Optional
from threading import Lock
mqtt.Client._create_lock = lambda self: None
class SmartBulb:
    """
    增强版智能灯泡设备（支持状态同步）
    """

    def __init__(self, device_id: str, broker: str, port: int = 1883):
        self.device_id = device_id
        self.broker = broker
        self.port = port

        # 设备状态
        self._state = "off"
        self._brightness = 0
        self._color = "white"
        self._last_updated = time.time()

        # 同步控制
        self._state_lock = Lock()
        self._pending_commands = {}  # 待确认命令
        self._command_timeout = 5    # 命令超时(秒)

        # 回调监听
        self.state_listeners = []

        # 初始化
        self._setup_logger()
        self._init_mqtt()

    def _setup_logger(self):
        """配置日志系统"""
        self.logger = logging.getLogger(f"Bulb_{self.device_id}")
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _init_mqtt(self):
        """初始化MQTT客户端"""
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"bulb_{self.device_id}_{int(time.time())}"
        )
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        # 主题设置
        self.base_topic = f"home/lights/{self.device_id}"

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        """MQTT断开连接回调"""
        if reason_code != mqtt.MQTT_ERR_SUCCESS:
            self.logger.warning(f"意外断开连接，代码: {reason_code}")
            self._attempt_reconnect()

    def _attempt_reconnect(self):
        """自动重连机制"""
        retry_count = 0
        while retry_count < 3:
            try:
                self.logger.info(f"尝试重连({retry_count + 1}/3)...")
                if self.connect():
                    return True
            except Exception as e:
                self.logger.error(f"重连失败: {str(e)}")
            retry_count += 1
            time.sleep(2)
        return False

    # ---------- 状态管理 ----------
    @property
    def state(self) -> str:
        with self._state_lock:
            return self._state

    @property
    def brightness(self) -> int:
        with self._state_lock:
            return self._brightness

    @property
    def color(self) -> str:
        with self._state_lock:
            return self._color

    def update_state(self, state: Optional[str] = None,
                     brightness: Optional[int] = None,
                     color: Optional[str] = None):
        """线程安全的状态更新"""
        with self._state_lock:
            if state is not None:
                self._state = state
            if brightness is not None:
                self._brightness = max(0, min(100, brightness))
            if color is not None:
                self._color = color
            self._last_updated = time.time()

    # ---------- MQTT通信 ----------
    def connect(self) -> bool:
        try:
            # 设置 MQTT 连接参数（增加超时和重试）
            self.client.connect(
                self.broker,
                self.port,
                keepalive=60,
                bind_address="" # 监听所有接口
            )
            # 必须调用 loop_start()，否则连接不会实际建立
            self.client.loop_start()

            # 等待连接真正建立（避免立即返回）
            retry = 0
            while not self.client.is_connected() and retry < 5:
                time.sleep(0.5)
                retry += 1

            if not self.client.is_connected():
                raise TimeoutError("MQTT 连接超时")

            return True
        except Exception as e:
            self.logger.error(f"MQTT 连接失败: {str(e)}")
            return False

    def disconnect(self):
        """安全断开 MQTT 连接"""
        if  self.client.is_connected():
            self.client.disconnect()
            self.client.loop_stop()  # 停止网络循环
            print("MQTT 连接已断开")

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """连接回调"""
        if reason_code.is_failure:
            self.logger.error(f"Connection failed: {reason_code}")
            return

        self.logger.info("MQTT connection established")
        # 订阅控制主题
        self.client.subscribe([
            (f"{self.base_topic}/control/+", 1),  # 控制命令
            (f"{self.base_topic}/state", 1)      # 状态更新
        ])
        self._publish_state()

    def _on_message(self, client, userdata, msg):
        """处理MQTT消息"""
        try:
            payload = json.loads(msg.payload.decode()) if msg.payload else {}

            if msg.topic.endswith("/state"):
                # 处理设备状态更新
                self._handle_state_update(payload)

            elif "/control/" in msg.topic:
                # 处理控制命令（模拟设备响应）
                command = msg.topic.split("/")[-1]
                self._simulate_device_response(command, payload)

        except Exception as e:
            self.logger.error(f"Message processing error: {str(e)}")

    def _handle_state_update(self, payload: Dict[str, Any]):
        """处理设备状态更新"""
        with self._state_lock:
            self._state = payload.get("state", self._state)
            self._brightness = payload.get("brightness", self._brightness)
            self._color = payload.get("color", self._color)
            self._last_updated = time.time()

        # 触发监听器
        current_state = self.current_state
        for listener in self.state_listeners:
            listener(current_state)

    def _simulate_device_response(self, command: str, payload: Dict[str, Any]):
        """模拟设备响应（实际项目应由物理设备实现）"""
        correlation_id = payload.get("correlation_id")

        if command == "set_state":
            new_state = payload.get("state", "off")
            self.update_state(state=new_state)

        elif command == "set_brightness":
            level = payload.get("brightness", 0)
            self.update_state(brightness=level)

        elif command == "set_color":
            color = payload.get("color", "white")
            self.update_state(color=color)

        # 模拟设备发布状态更新
        self._publish_state(correlation_id=correlation_id)

    def _publish_state(self, correlation_id: Optional[str] = None):
        """发布当前状态"""
        state = self.current_state
        if correlation_id:
            state["correlation_id"] = correlation_id

        self.client.publish(
            f"{self.base_topic}/state",
            payload=json.dumps(state),
            qos=1,
            retain=True
        )
        self.logger.debug(f"Published state: {state}")

    def _publish_control_command(self, command: str, payload: Optional[Dict] = None) -> bool:
        """发布控制命令（带确认机制）"""
        correlation_id = f"cmd_{time.time()}"
        payload = payload or {}
        payload["correlation_id"] = correlation_id

        with self._state_lock:
            self._pending_commands[correlation_id] = {
                "command": command,
                "timestamp": time.time()
            }

        topic = f"{self.base_topic}/control/{command}"
        try:
            self.client.publish(
                topic,
                payload=json.dumps(payload),
                qos=1
            )
            self.logger.info(f"Published command to {topic}")

            # 等待确认
            '''
            start_time = time.time()
            while correlation_id in self._pending_commands:
                if time.time() - start_time > self._command_timeout:
                    del self._pending_commands[correlation_id]
                    raise TimeoutError("Device response timeout")
                time.sleep(0.1)
                '''

            return True

        except Exception as e:
            self.logger.error(f"Command publish failed: {str(e)}")
            return False

    @property
    def current_state(self) -> Dict[str, Any]:
        """获取当前状态快照"""
        with self._state_lock:
            return {
                "device_id": self.device_id,
                "state": self._state,
                "brightness": self._brightness,
                "color": self._color,
                "last_updated": self._last_updated
            }

    def add_state_listener(self, callback):
        """添加状态变更监听器"""
        self.state_listeners.append(callback)

    def run(self):
        """运行设备"""
        self.connect()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.client.disconnect()


if __name__ == '__main__':
    bulb = SmartBulb(
        device_id="living_room_lamp",
        broker="test.mosquitto.org"
    )
    bulb.run()