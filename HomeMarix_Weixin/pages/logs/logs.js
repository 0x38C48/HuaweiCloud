const api = require('../../utils/api');

Page({
  data: {
    token: '',
    devices: []
  },

  onLoad() {
    api.request('/api/login', 'POST', { username: 'demo', password: 'demo' })
      .then(res => {
        this.setData({ token: res.token });
        this.fetchDevices();
        this.connectSocket();
      })
      .catch(err => {
        wx.showToast({ title: '登录失败', icon: 'none' });
      });
  },

  fetchDevices() {
    api.request('/api/devices', 'GET', {}, this.data.token)
      .then(res => {
        this.setData({ devices: res.devices });
      })
      .catch(err => {
        console.error(err);
        wx.showToast({ title: '获取设备失败', icon: 'none' });
      });
  },

  refresh() { this.fetchDevices(); },

  onToggle(e) {
    const id = e.detail.id;
    api.request(`/api/devices/${id}/control`, 'POST', { action: 'toggle' }, this.data.token)
      .then(() => this.fetchDevices())
      .catch(() => wx.showToast({ title: '控制失败', icon: 'none' }));
  },

  onSetMeta(e) {
    const { id, payload } = e.detail;
    api.request(`/api/devices/${id}/control`, 'POST', { action: 'set', payload }, this.data.token)
      .catch(() => wx.showToast({ title: '设置失败', icon: 'none' }));
  },

  connectSocket() {
    const url = 'wss://your-huawei-backend.example.com';
    const socketTask = wx.connectSocket({ url });
    socketTask.onOpen(() => {
      console.log('socket open');
      socketTask.send({ data: JSON.stringify({ type: 'get_devices' }) });
    });
    socketTask.onMessage((msg) => {
      try {
        const d = JSON.parse(msg.data);
        if (d.type === 'devices'){
          this.setData({ devices: d.payload });
        } else if (d.type === 'device_update'){
          const updated = d.payload;
          const arr = this.data.devices.map(it => it.id === updated.id ? updated : it);
          this.setData({ devices: arr });
        }
      } catch(e){
        console.warn('socket parse error', e);
      }
    });
    socketTask.onClose(() => console.log('socket close'));
    socketTask.onError(err => console.error('socket error', err));
  }
});