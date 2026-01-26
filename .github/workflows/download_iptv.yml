import requests
import os
import random
from datetime import datetime

# 配置
TARGET_URL = "https://iptv.cqshushu.com/"
SAVE_DIR = "web_pages"
UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

def download_homepage():
    os.makedirs(SAVE_DIR, exist_ok=True)
    headers = {
        "User-Agent": random.choice(UA_LIST),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        print(f"正在尝试下载: {TARGET_URL}")
        # 增加随机延迟模拟真人
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        response.raise_for_status() 
        response.encoding = 'utf-8' # 强制编码防止乱码

        # 生成文件名：homepage_20240520_1030.html
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"homepage_{timestamp}.html"
        file_path = os.path.join(SAVE_DIR, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        
        print(f"✅ 下载成功！文件大小: {len(response.text)} 字节")
        print(f"📂 已保存至: {file_path}")

    except Exception as e:
        print(f"❌ 下载失败: {e}")

if __name__ == "__main__":
    download_homepage()
