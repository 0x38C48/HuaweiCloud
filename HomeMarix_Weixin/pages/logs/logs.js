// logs.js
Page({
    data: {
      devices: [
        { id: 1, name: '设备1', status: '未启动', isOn: false },
        { id: 2, name: '设备2', status: '未启动', isOn: false }
      ],
    },
  
    // 切换设备的状态
    toggleDeviceStatus: function (e) {
        const deviceId = e.target.dataset.id; // 获取设备的 id
        const devices = this.data.devices.map(device => {
          if (device.id === deviceId) {
            device.isOn = !device.isOn;
            device.status = device.isOn ? '已启动' : '已关闭';
          }
          return device;
        });
      
        this.setData({
          devices: devices
        });
    },
      
  
    // 添加新设备
    addDevice: function () {
      const newDeviceId = this.data.devices.length + 1;  // 新设备 ID
      const newDevice = {
        id: newDeviceId,
        name: `设备${newDeviceId}`,
        status: '未启动',
        isOn: false
      };
  
      this.setData({
        devices: [...this.data.devices, newDevice]  // 将新设备添加到设备列表
      });
    },
  });
  