Component({
  properties: {
    device: { type: Object, value: {} }
  },
  methods: {
    onToggle(e) {
      this.triggerEvent('toggle', { id: this.data.device.id });
    }
  }
});