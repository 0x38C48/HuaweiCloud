import paho.mqtt.client as mqtt
import json
import time
import logging
from threading import Lock
from typing import Dict, Any, Optional

class SmartLock:
    """
    智能门锁设备
    """

    def __init__(self, device_id: str, broker: str, port: int = 1883):
        self.device_id = device_id
        self.broker = broker
        self.port = port

        # 设备状态
        self._locked = True
        self._last_updated = time.time()

        # 同步控制
        self._state_lock = Lock()
        self._pending_commands = {}
        self._command_timeout = 5

        # 回调监听
        self.state_listeners = []

        # 初始化
        self._setup_logger()
        self._init_mqtt()

    def _setup_logger(self):
        """配置日志系统"""
        self.logger = logging.getLogger(f"Lock_{self.device_id}")
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _init_mqtt(self):
        """初始化MQTT客户端"""
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"lock_{self.device_id}_{int(time.time())}"
        )
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        # 主题设置
        self.base_topic = f"home/locks/{self.device_id}"

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
    def locked(self) -> bool:
        with self._state_lock:
            return self._locked


    def set_lock(self, locked: bool):
        """设置门锁状态"""
        with self._state_lock:
            self._locked = locked
            self._last_updated = time.time()
        self._publish_state()



    # ---------- MQTT通信 ----------
    def connect(self) -> bool:
        """连接MQTT代理"""
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            self.logger.info(f"Connected to {self.broker}:{self.port}")
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {str(e)}")
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
        self.client.subscribe([
            (f"{self.base_topic}/control/lock", 1)
        ])
        self._publish_state()

    def _on_message(self, client, userdata, msg):
        """处理MQTT消息"""
        try:
            payload = json.loads(msg.payload.decode()) if msg.payload else {}
            command = msg.topic.split('/')[-1]

            if command == "lock":
                self.set_lock(payload.get("locked", True))

        except Exception as e:
            self.logger.error(f"Message processing error: {str(e)}")

    def _publish_state(self):
        """发布当前状态"""
        state = {
            "locked": self.locked,
            "timestamp": self._last_updated
        }
        self.client.publish(
            f"{self.base_topic}/state",
            payload=json.dumps(state),
            qos=1,
            retain=True
        )

    @property
    def current_state(self) -> Dict[str, Any]:
        """获取当前状态快照"""
        with self._state_lock:
            return {
                "device_id": self.device_id,
                "locked": self._locked,
                "last_updated": self._last_updated
            }

    def run(self):
        """运行设备"""
        self.connect()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.client.disconnect()
