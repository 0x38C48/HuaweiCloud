from flask_socketio import SocketIO

from flask import Flask, request, jsonify

import logging
from typing import Dict, Any

from Cloud.client.controller.Manager import DeviceManager
from Cloud.client.entity.Bulb import SmartBulb
from Cloud.client.entity.Lock import SmartLock
from Cloud.client.entity.Sensor import EnvironmentSensor

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
manager = DeviceManager()

# ---------- 设备管理接口 ----------
@app.route('/api/devices', methods=['POST'])
def device_collection():
    data = request.json
    try:
        # 必选参数
        required = {'type', 'device_id'}
        if not required.issubset(data):
            return jsonify({"error": f"缺少必要参数: {required - set(data.keys())}"}), 400

        # 可选参数默认值
        params = {
            'broker': data.get('broker', 'test.mosquitto.org'),
            'port': data.get('port', 1883)
        }

        # 创建设备
        success = manager.create_device(
            device_type=data['type'],
            device_id=data['device_id'],
            **params
        )

        if not success:
            return jsonify({"error": "device_connection_failed"}), 502

        return jsonify(manager.get_device(data['device_id']).current_state), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/devices/<device_id>', methods=['DELETE'])
def delete_device(device_id: str):
    if manager.delete_device(device_id):
        return jsonify({"status": "deleted"})
    return jsonify({"error": "device_not_found"}), 404

@app.route('/api/devices/view', methods=['GET'])
def show_device():
    try:
        return jsonify(manager.list_devices())
    except Exception as e:
        logging.error(f"Control error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "get_failed",
            "message": str(e)
        }), 500


@app.route('/api/devices/<device_id>/control', methods=['POST'])
def control_device(device_id: str):
    try:
        data = request.json
        device = manager.get_device(device_id)

        if not device:
            return jsonify({"error": "device_not_found"}), 404

        # 智能灯泡专用控制
        if isinstance(device, SmartBulb):
            # 构造控制参数
            control_params = {}
            if 'state' in data:
                control_params['state'] = data['state']
            if 'brightness' in data:
                control_params['brightness'] = data['brightness']
            if 'color' in data:
                control_params['color'] = data['color']

            if control_params:
                # 统一调用设备控制方法
                device.update_state(**control_params)
                return jsonify(device.current_state)
            else:
                return jsonify({"error": "no_valid_parameters"}), 400

        # 其他设备类型的通用控制路由
        if isinstance(device,SmartLock):
            locked=data['locked']
            if locked==0 or locked==1:
                device.set_lock(locked)
                return jsonify(device.current_state)
            else:
                return jsonify({"error": "no_valid_parameters"}), 400

        if isinstance(device,EnvironmentSensor):
            return jsonify({"error": "sensor could not be controlled"}), 400

        return jsonify({"error": "invalid_command"}), 400

    except Exception as e:
        logging.error(f"Control error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "control_failed",
            "message": str(e)
        }), 500


# ---------- 类型专属接口 ----------
@app.route('/api/devices/<device_id>/state', methods=['GET'])
def get_state(device_id: str):
    try:
        device = manager.get_device(device_id)
        if not device:
            return jsonify({"error": "device could not be found"}), 404
        else:return jsonify(device.current_state)
    except Exception as e:
        logging.error(f"Control error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "state_get_failed",
            "message": str(e)
        }), 500


# ---------- WebSocket ----------
@socketio.on('connect')
def handle_connect():
    logging.info(f"Client connected: {request.sid}")

@socketio.on('subscribe')
def handle_subscribe(data: Dict):
    device_id = data.get('device_id')
    if device := manager.get_device(device_id):
        socketio.emit('device_update', {
            'device_id': device_id,
            'state': device.current_state
        })

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    socketio.run(app, host='127.0.0.1', port=5000, debug=True,allow_unsafe_werkzeug=True)