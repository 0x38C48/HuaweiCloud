Page({
  data: {
    token: '',
    username: '',
    password: '',
    devices: []
  },

  onLoad() {
    this.initDevices();
    this.simulateUpdates();
  },

  // 初始化设备
  initDevices() {
    this.setData({
      devices: [
        { id: 1, name: '灯泡', state: 'off' },
        { id: 2, name: '风扇', state: 'off' },
        { id: 3, name: '空调', state: 'off' }
      ]
    });
  },

  // 模拟实时更新
  simulateUpdates() {
    setInterval(() => {
      const devices = this.data.devices.map(d => {
        if (Math.random() > 0.7) {
          d.state = d.state === 'on' ? 'off' : 'on';
        }
        return d;
      });
      this.setData({ devices });
    }, 5000);
  },

  // 登录表单输入
  onUsernameInput(e) { this.setData({ username: e.detail.value }); },
  onPasswordInput(e) { this.setData({ password: e.detail.value }); },

  // 登录
  login() {
    const { username, password } = this.data;
    if (username === 'demo' && password === 'demo') {
      this.setData({ token: 'local-token-123' });
      wx.showToast({ title: '登录成功', icon: 'success' });
    } else {
      wx.showToast({ title: '用户名或密码错误', icon: 'none' });
    }
  },

  // 切换设备状态
  onToggle(e) {
    const id = e.currentTarget.dataset.id;
    const devices = this.data.devices.map(d => {
      if (d.id === id) d.state = d.state === 'on' ? 'off' : 'on';
      return d;
    });
    this.setData({ devices });
  }
});
