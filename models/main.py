import requests
import json
from dotenv import load_dotenv
import os
from datetime import datetime

# 1. 加载配置（敏感信息从.env文件读取，记得创建包含关键信息的.env文件在当前目录下）

load_dotenv()  # 加载.env文件
'''
# .env文件内容
DEEPSEEK_API_KEY=your_deepseek_api_key_here  # 需申请，可手动改名，创建在models目录下
'''
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")  # DeepSeek API密钥(实例，我还没有找到华为云相关API，商店里都要付费，之后替换成华为相关的API）
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # DeepSeek对话API地址（同，手动替换）

# 项目其他模块接口（需与团队确认实际地址）
STORAGE_API_URL = "http://localhost:8080/api/storage/get_user_preference"  # xjh存储模块-获取用户偏好
IOT_EVENT_API_URL = "http://localhost:8081/api/iot/"  # wyt IoT模块-获取设备事件
MINIPROGRAM_PUSH_URL = "http://localhost:8082/api/miniprogram/push_dialog"  # zxj小程序-推送对话

# 2. 工具函数：对接其他模块（存储、IoT）

def get_user_preference(user_id: str) -> dict:
    """
    调用xjh的存储查找功能，获取用户个性化偏好（如空调温度、灯光亮度）
    :param user_id: 用户唯一ID（与xjh确认格式，如"user_001"）
    :return: 用户偏好字典（如{"aircon_temp":26, "light_brightness":80}）
    """
    try:
        # 发送GET请求（我不知道xjh数据库搞怎么一个格式，先写个示例，下同）
        response = requests.get(
            url=STORAGE_API_URL,
            params={"user_id": user_id, "date": datetime.now().strftime("%Y-%m-%d")}  # 带日期参数
        )
        response.raise_for_status()  # 若请求失败（如404、500），抛出异常
        return response.json()  # 返回用户偏好数据
    except Exception as e:
        print(f"获取用户{user_id}偏好失败：{str(e)}")
        return {"aircon_temp": 26, "light_brightness": 70}  # 默认值，用于没有信息的用户


def get_latest_iot_event() -> dict:
    """
    调用wyt的IoT模块，获取最新设备事件（如设备故障、家人回家触发）
    :return: 设备事件字典（需与wyt确认决策格式和示例结构，一个人还是不太能写）
    """
    try:
        response = requests.get(url=IOT_EVENT_API_URL+"get_device_event")
        response.raise_for_status() #wyt可以修改一下相关的格式
        return response.json()  # 示例返回：{"event_type":"device_fault", "device_id":"ac_001", "user_id":"user_001"}
    except Exception as e:
        print(f"获取IoT设备事件失败：{str(e)}")
        return {"event_type": "none", "device_id": "", "user_id": ""}  # 无事件默认值


# 3.DeepSeek API调用生成个性化对话

def call_deepseek_api(prompt: str) -> str:
    """
    调用DeepSeek通用模型API，生成对话内容，支撑主动触发与个性化反馈，后续可换成华为云相关API服务
    :param prompt: 对话生成提示词（含场景、用户偏好）
    :return: 模型生成的对话文本
    """
    # 构建DeepSeek API请求参数（参考官方文档格式）
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"  # 身份认证
    }
    payload = {
        "model": "deepseek-chat",  # 模型名称，确认实际支持的模型名
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,  # 随机性（0-1）
        "max_tokens": 200  # 最大生成文本token数
    }

    try:
        response = requests.post(url=DEEPSEEK_API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()  # 提取生成的对话
    except Exception as e:
        print(f"DeepSeek API调用失败：{str(e)}")
        return "服务器繁忙，请稍后再试的说~"  # 经典



# 4. 主动触发式AI对话（关联创新点）

def trigger_ai_dialog() -> None:
    """
    主动触发逻辑：根据IoT/预警系统事件，生成个性化对话并推送到小程序
    """
    # 步骤1：获取最新触发事件（如IoT设备故障、家人回家）
    latest_event = get_latest_iot_event()
    event_type = latest_event.get("event_type")
    user_id = latest_event.get("user_id")
    device_id = latest_event.get("device_id")

    # 步骤2：仅处理需要触发对话的事件（过滤无需对话的场景，如陌生人闯入由预警系统警报）
    if event_type not in ["device_fault", "family_return", "device_risk"]:
        print(f"事件类型{event_type}无需触发AI对话，跳过")
        return

    # 步骤3：获取用户偏好，生成个性化提示词，后续运维可以增加更多场景
    user_preference = get_user_preference(user_id)
    if event_type == "family_return":
        # 场景1：家人回家
        prompt = f"""
        你是家居管家AI，用户{user_id}刚回家，其偏好设置为：空调温度{user_preference['aircon_temp']}℃、灯光亮度{user_preference['light_brightness']}%。
        请生成1句主动欢迎对话，包含是否帮其开启对应设备的询问，语气亲切自然，不超过50字。
        """
    elif event_type == "device_fault":
        # 场景2：设备故障（触发提醒+简单建议）
        prompt = f"""
        你是家居管家AI，用户{user_id}的设备{device_id}出现故障。请生成1句提醒对话，建议检查设备，语气友好，不超过40字。
        """
    elif event_type == "device_risk":
        # 场景3：设备风险（如燃气泄漏，触发紧急提醒）
        prompt = f"""
        你是家居管家AI，用户{user_id}的设备{device_id}存在安全风险。请生成1句紧急提醒，建议立即处理，不超过30字。
        """
    else:
        prompt = "欢迎使用家居管家，有什么可以帮你的吗？"  # 兜底提示词

    # 调用DeepSeek生成对话
    dialog_content = call_deepseek_api(prompt)
    print(f"生成主动对话：{dialog_content}")

    # 推送到zxj的小程序（调用小程序接口）
    push_data = {
        "user_id": user_id,
        "dialog_content": dialog_content,
        "push_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        response = requests.post(
            url=MINIPROGRAM_PUSH_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(push_data)
        )
        response.raise_for_status()
        print(f"对话已推送到用户{user_id}的小程序，推送结果：{response.json()}")
    except Exception as e:
        print(f"推送小程序失败：{str(e)}")


# 5. 测试入口，本地运行验证，可以在API申请完毕后测试

if __name__ == "__main__":
    # 本地测试：模拟触发1次AI对话（可替换为实际事件）
    print("=== 开始测试主动触发AI对话 ===")
    trigger_ai_dialog()
    print("=== 测试结束 ===")