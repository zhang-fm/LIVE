import os
import re
import base64
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def decode_ip(data):
    try:
        return base64.b64decode(data).decode('utf-8')
    except: return None

def main():
    chrome_options = Options()
    chrome_options.add_argument('--headless') # 无头模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # 模拟真实浏览器 User-Agent
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    print("🌐 启动 Chrome 浏览器并加载页面...")
    try:
        driver.get("https://iptv.cqshushu.com/")
        
        # 关键：等待 10 秒，让 JS 挑战页面自动刷新进入主页
        print("⏳ 等待 JS 验证跳转 (10s)...")
        time.sleep(10)
        
        html = driver.page_source
        print(f"📄 页面快照: {html[:150].strip()}...")

        # 提取 Base64 IP
        found_ips = set()
        candidates = re.findall(r"['\"]([A-Za-z0-9+/=]{8,})['\"]", html)
        for c in candidates:
            ip = decode_ip(c)
            if ip and re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
                found_ips.add(ip)

        print(f"📍 发现有效 IP: {list(found_ips)}")
        # ... 后续下载逻辑 ...
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
