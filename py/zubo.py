import requests
import re
import os
import time
import base64
import random
from datetime import datetime

# ======================
# 配置区
# ======================
HOME_URL = "https://iptv.cqshushu.com/"
OUTPUT_DIR = "zubo"
HISTORY_FILE = os.path.join(OUTPUT_DIR, "history.txt")
MAX_IP_COUNT = 6
TIMEOUT = 12

PRIMARY_MULTICAST_PORTS = [
    6636, 16888, 5002, 8055, 8288, 8880, 5555, 55555, 7000, 6003, 9999, 8012, 10000, 8888, 4022, 8188, 8022, 7777, 5146, 5140, 4056, 12320, 
    10000, 8080, 8000, 9901, 8090, 8181, 1234, 4000, 4001, 5148, 12345, 8805, 8187, 9926, 8222, 8808, 8883, 8686, 8188, 4023, 8848, 6666, 
    9000, 9001, 888, 9003, 8082, 20443, 85, 8081, 8001, 8899
]

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

# ======================
# 核心逻辑：周一清理 & 历史记录
# ======================

def manage_history():
    """简单粗暴：周一就删表"""
    # 0代表周一
    if datetime.now().weekday() == 0:
        if os.path.exists(HISTORY_FILE):
            print("📅 今天是周一，简单粗暴清理历史 IP 表！")
            os.remove(HISTORY_FILE)
    
    history_ips = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    history_ips.add(line.split(':')[0].strip())
    return history_ips

def save_history(ip, port):
    """记录成功抓取的 IP 和端口"""
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{ip}:{port}\n")

# ======================
# 抓取与探测
# ======================

def get_headers():
    return {"User-Agent": random.choice(UA_LIST), "Referer": "https://fofa.info/"}

def get_fofa_ports(ip):
    time.sleep(random.uniform(8, 15))
    try:
        query = base64.b64encode(ip.encode()).decode()
        res = requests.get(f"https://fofa.info/result?qbase64={query}", headers=get_headers(), timeout=15)
        # 提取端口
        ports = set(re.findall(rf'{ip}:(\d+)', res.text) + re.findall(r'port-item.*?(\d+)</a>', res.text, re.S))
        return sorted([int(p) for p in ports if int(p) not in {22, 23, 443, 80, 53, 3306, 3389}])
    except: return []

def scan_ip_port(ip, port):
    url = f"https://iptv.cqshushu.com/?s={ip}:{port}&t=multicast&channels=1&download=m3u"
    try:
        time.sleep(random.uniform(2, 4))
        res = requests.get(url, headers=get_headers(), timeout=TIMEOUT)
        if res.status_code == 200 and "#EXTINF" in res.text:
            return res.text
    except: pass
    return None

# ======================
# 执行流程
# ======================

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    history_ips = manage_history()
    
    # 1. 获取首页 IP 列表
    try:
        r = requests.get(HOME_URL, headers=get_headers(), timeout=TIMEOUT)
        ips = list(dict.fromkeys(re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", r.text)))
        target_ips = [ip for ip in ips if not ip.startswith("127")][-MAX_IP_COUNT:]
    except: return

    # 2. 过滤已存在的 IP
    new_ips = [ip for ip in target_ips if ip not in history_ips]
    if not new_ips:
        print("✅ 没发现新 IP，全部跳过。")
        return

    print(f"🎯 开始探测新 IP: {new_ips}")

    for ip in new_ips:
        print(f"\n📡 正在处理: {ip}")
        f_ports = get_fofa_ports(ip)
        # 整合端口：FOFA 发现的端口 + 常用备选端口
        test_ports = f_ports + [p for p in PRIMARY_MULTICAST_PORTS if p not in f_ports]

        success_count = 0 
        for port in test_ports:
            print(f" ➜ 尝试端口 {port} ... ", end="", flush=True)
            content = scan_ip_port(ip, port)
            
            if content:
                print("✅ 成功！")
                with open(os.path.join(OUTPUT_DIR, f"raw_{ip}_{port}.m3u"), "w", encoding="utf-8") as f:
                    f.write(content)
                save_history(ip, port)
                success_count += 1
                
                # --- 特殊设定：如果该 IP 已经抓到 2 个不同端口的内容，就停止该 IP 的探测 ---
                if success_count >= 2:
                    print(f" 💡 该 IP 已抓取到 2 个有效端口，停止后续尝试。")
                    break
            else:
                print("✕")
        
        time.sleep(random.uniform(5, 10))

if __name__ == "__main__":
    main()
