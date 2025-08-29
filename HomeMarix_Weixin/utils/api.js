const BASE_URL = 'https://your-huawei-backend.example.com'; // 改成你的后端地址

function request(path, method='GET', data={}, token=''){
  const headers = {};
  if (token) headers['Authorization'] = 'Bearer ' + token;
  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + path,
      method,
      data,
      header: headers,
      success(res){
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data);
        else reject(res);
      },
      fail(err){ reject(err); }
    });
  });
}

module.exports = { request };