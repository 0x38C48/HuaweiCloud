from flask_socketio import SocketIO
from typing import Dict, List
from Cloud.client.entity.Bulb import SmartBulb
from Cloud.client.entity.Sensor import EnvironmentSensor
from Cloud.client.entity.Lock import SmartLock
import logging

class DeviceManager:
    """
    统一设备管理器（支持灯泡、传感器、门锁）
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.devices: Dict[str, object] = {}
            cls._instance._setup_logger()
        return cls._instance

    def _setup_logger(self):
        """配置日志系统"""
        self.logger = logging.getLogger("DeviceManager")
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def create_device(self, device_type: str, device_id: str, **kwargs) -> bool:
        """增强版创建设备"""
        required_params = {
            'light': ['broker', 'port'],
            'sensor': ['broker'],
            'lock': ['broker']
        }

        # 参数校验
        missing = [p for p in required_params.get(device_type, []) if p not in kwargs]
        if missing:
            raise ValueError(f"缺少必要参数: {missing}")

        # 创建设备实例
        device_classes = {
            'light': SmartBulb,
            'sensor': EnvironmentSensor,
            'lock': SmartLock
        }
        device = device_classes[device_type](device_id,**kwargs)
        device.connect()

        self.devices[device_id] = device
        return True



    def delete_device(self, device_id: str) -> bool:
        """删除设备"""
        if device_id not in self.devices:
            return False

        self.devices[device_id].disconnect()
        del self.devices[device_id]
        return True

    def get_device(self, device_id: str):
        """获取设备实例"""
        return self.devices.get(device_id)

    def _handle_state_update(self, device_id: str, state: Dict[str, any]):
        """推送状态更新到前端"""
        SocketIO().emit('device_update', {
            'device_id': device_id,
            'state': state
        })

    def list_devices(self, filter_type: str = None) -> List[Dict[str, any]]:
        """列出所有设备"""
        return [
            {
                "device_id": dev_id,
                "type": "light" if isinstance(dev, SmartBulb) else
                "sensor" if isinstance(dev, EnvironmentSensor) else "lock",
                "state": dev.current_state
            }
            for dev_id, dev in self.devices.items()
            if not filter_type or isinstance(dev, self._get_device_class(filter_type))
        ]

    def _get_device_class(self, device_type: str):
        """获取设备类"""
        type_map = {
            "light": SmartBulb,
            "sensor": EnvironmentSensor,
            "lock": SmartLock
        }
        return type_map.get(device_type)

