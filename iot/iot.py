
import json
import time
from datetime import datetime
from enum import Enum
import threading
import random  # 用于模拟设备事件，实际应用中移除

# 设备事件类型枚举
class EventType(Enum):
    NONE = "none"
    DEVICE_FAULT = "device_fault"
    FAMILY_RETURN = "family_return"
    DEVICE_RISK = "device_risk"
    DEVICE_STATUS_UPDATE = "device_status_update"
    TEMPERATURE_ALERT = "temperature_alert"
    HUMIDITY_ALERT = "humidity_alert"

# 设备类型枚举
class DeviceType(Enum):
    AIR_CONDITIONER = "air_conditioner"
    LIGHT = "light"


# IoT模块主类



class IoTModule:
    def __init__(self, api_port=8081):
        self.api_url = f"http://localhost:{api_port}/api/iot"
        self.devices = self._initialize_devices()
        self.event_listeners = []

        # 启动设备状态监控线程
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._device_monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def _initialize_devices(self):
        """初始化设备列表（实际应用中应从数据库加载）"""
        return {
            "ac_001": {
                "type": DeviceType.AIR_CONDITIONER,
                "name": "客厅空调",
                "status": "off",
                "temperature": 26,
                "last_update": datetime.now(),
                "user_id": "user_001"
            },
            "light_001": {
                "type": DeviceType.LIGHT,
                "name": "主卧灯",
                "status": "off",
                "brightness": 70,
                "last_update": datetime.now(),
                "user_id": "user_001"
            },
            "lock_001": {
                "type": DeviceType.DOOR_LOCK,
                "name": "大门锁",
                "status": "locked",
                "last_update": datetime.now(),
                "user_id": "user_001"
            },

            "temp_001": {
                "type": DeviceType.TEMPERATURE_SENSOR,
                "name": "客厅温度传感器",
                "status": "normal",
                "value": 25,
                "last_update": datetime.now(),
                "user_id": "user_001"
            }
        }

    def _device_monitor_loop(self):
        """设备监控循环，定期检查设备状态"""
        while self.monitoring:
            try:
                # 检查每个设备的状态
                for device_id, device_info in self.devices.items():
                    # 模拟设备状态变化（实际应用中应通过实际设备接口获取）
                    if random.random() < 0.1:  # 10%的概率发生状态变化
                        self._simulate_device_event(device_id, device_info)

                # 休眠一段时间再检查
                time.sleep(5)
            except Exception as e:
                print(f"设备监控循环出错: {e}")
                time.sleep(10)  # 出错后等待更长时间

    def _simulate_device_event(self, device_id, device_info):
        """模拟设备事件（实际应用中应替换为真实设备通信）"""
        device_type = device_info["type"]

        if device_type == DeviceType.DOOR_LOCK:
                self._trigger_event(
                    EventType.FAMILY_RETURN,
                    device_id,
                    device_info["user_id"],
                    {"action": "unlocked"}
                )

        elif device_type == DeviceType.AIR_CONDITIONER:
            self._trigger_event(
                EventType.DEVICE_FAULT,
                device_id,
                device_info["user_id"],
                {"error_code": "E102", "previous_status": device_info["status"]}
            )

        elif device_type == DeviceType.GAS_SENSOR:
             self._trigger_event(
                EventType.DEVICE_RISK,
                device_id,
                device_info["user_id"],
                {"gas_level": round(random.uniform(0.5, 2.0), 2)}
            )

    def _trigger_event(self, event_type, device_id, user_id, extra_data=None):
        """触发设备事件并通知所有监听器"""
        event_data = {
            "event_type": event_type.value,
            "device_id": device_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }

        if extra_data:
            event_data.update(extra_data)

        # 更新设备状态
        if event_type == EventType.DEVICE_STATUS_UPDATE and "status" in extra_data:
            self.devices[device_id]["status"] = extra_data["status"]
            self.devices[device_id]["last_update"] = datetime.now()

        # 通知所有监听器
        for listener in self.event_listeners:
            try:
                listener(event_data)
            except Exception as e:
                print(f"通知事件监听器出错: {e}")

        print(f"触发事件: {event_data}")
        return event_data

    def add_event_listener(self, listener):
        """添加事件监听器"""
        self.event_listeners.append(listener)

    def get_device_event(self):
        """提供给外部API的获取设备事件方法（与您的AI模块对接）"""
        # 在实际应用中，这里应该返回真实的事件队列
        # 这里返回模拟事件用于测试
        events = []
        device_id = random.choice(list(self.devices.keys()))
        device_info = self.devices[device_id]
        event_type = random.choice([EventType.DEVICE_FAULT, EventType.FAMILY_RETURN, EventType.DEVICE_RISK])
        events.append(self._trigger_event(event_type, device_id, device_info["user_id"]))

        return events[0] if events else {"event_type": EventType.NONE.value, "device_id": "", "user_id": ""}

    def get_device_status(self, device_id):
        """获取设备状态"""
        if device_id in self.devices:
            return self.devices[device_id]
        return None

    def control_device(self, device_id, action, value=None):
        """控制设备（供AI模块调用）"""
        if device_id not in self.devices:
            return {"success": False, "error": "设备不存在"}

        device = self.devices[device_id]

        try:
            if device["type"] == DeviceType.AIR_CONDITIONER:
                if action == "turn_on":
                    device["status"] = "on"
                elif action == "turn_off":
                    device["status"] = "off"
                elif action == "set_temperature" and value is not None:
                    device["temperature"] = value

            elif device["type"] == DeviceType.LIGHT:
                if action == "turn_on":
                    device["status"] = "on"
                elif action == "turn_off":
                    device["status"] = "off"
                elif action == "set_brightness" and value is not None:
                    device["brightness"] = value

            device["last_update"] = datetime.now()

            # 触发状态更新事件
            self._trigger_event(
                EventType.DEVICE_STATUS_UPDATE,
                device_id,
                device["user_id"],
                {"status": device["status"], "action": action, "value": value}
            )

            return {"success": True, "message": "设备控制成功"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user_devices(self, user_id):
        """获取用户的所有设备"""
        return {dev_id: info for dev_id, info in self.devices.items() if info["user_id"] == user_id}

# Flask API实现（供其他模块调用）
from flask import Flask, request, jsonify

app = Flask(__name__)
iot_module = IoTModule()

@app.route('/api/iot/get_device_event', methods=['GET'])
def get_device_event():
    """获取设备事件（与您的AI模块对接）"""
    event = iot_module.get_device_event()
    return jsonify(event)

@app.route('/api/iot/device_status', methods=['GET'])
def get_device_status():
    """获取设备状态"""
    device_id = request.args.get('device_id')
    if not device_id:
        return jsonify({"error": "缺少device_id参数"}), 400

    status = iot_module.get_device_status(device_id)
    if status:
        return jsonify(status)
    else:
        return jsonify({"error": "设备不存在"}), 404

@app.route('/api/iot/control_device', methods=['POST'])
def control_device():
    """控制设备"""
    data = request.json
    device_id = data.get('device_id')
    action = data.get('action')
    value = data.get('value')

    if not device_id or not action:
        return jsonify({"error": "缺少必要参数"}), 400

    result = iot_module.control_device(device_id, action, value)
    return jsonify(result)

@app.route('/api/iot/user_devices', methods=['GET'])
def get_user_devices():
    """获取用户的所有设备"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "缺少user_id参数"}), 400

    devices = iot_module.get_user_devices(user_id)
    return jsonify(devices)

if __name__ == '__main__':
    # 启动IoT模块API服务
    app.run(port=8081, debug=True)