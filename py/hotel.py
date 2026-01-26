import requests
import re
import os
import time
import base64
import random
import sys
from datetime import datetime

# ======================
# 配置区
# ======================
LOCAL_SOURCE = "data/shushu_home.html"
OUTPUT_DIR = "hotel"
HISTORY_FILE = os.path.join(OUTPUT_DIR, "hotel_history.txt")
MAX_IP_COUNT = 6
TIMEOUT = 12

# 酒店源高频端口
PRIMARY_PORTS = [8082, 9901, 888, 9001, 9003, 9888, 8080, 8000, 9999, 8888, 8090, 8081, 8181, 8899, 8001, 85, 808, 50001, 20443]

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
]

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

def manage_hotel_history():
    if datetime.now().weekday() == 0 and os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    history_ips = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line: history_ips.add(line.split(':')[0].strip())
    return history_ips

def scan_ip_port(ip, port):
    url = f"https://iptv.cqshushu.com/index.php?s={ip}:{port}&t=hotel&channels=1&download=m3u"
    try:
        time.sleep(random.uniform(1.0, 1.5))
        res = requests.get(url, headers={"User-Agent": random.choice(UA_LIST)}, timeout=TIMEOUT)
        return res.text if (res.status_code == 200 and "#EXTINF" in res.text) else None
    except: return None

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    history_ips = manage_hotel_history()
    
    if not os.path.exists(LOCAL_SOURCE):
        log(f"❌ 找不到文件: {LOCAL_SOURCE}"); return

    try:
        with open(LOCAL_SOURCE, "r", encoding="utf-8") as f:
            html = f.read()
        
        # 1. 切割酒店区域
        if "Hotel IPTV" in html:
            hotel_area = html.split("Hotel IPTV")[1].split('group-section')[0]
            log("🎯 已定位到酒店源数据块")
        else:
            hotel_area = html
            log("⚠️ 未发现标记，全局扫描")

        # 2. 提取所有可能的 IP (明文 + 加密)
        # 2.1 先找明文 IP
        ips = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", hotel_area)
        
        # 2.2 关键：找隐藏在引号里的 Base64 字符串
        # 这种网页通常把 IP 加密后放在 play('...') 或者 s=... 后面
        potential_b64 = re.findall(r'[\'"]([A-Za-z0-9+/]{12,32}={0,2})[\'"]', hotel_area)
        for b in potential_b64:
            try:
                decoded = base64.b64decode(b).decode('utf-8')
                if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", decoded):
                    ips.append(decoded)
            except: continue

        # 3. 整理并过滤
        public_ips = []
        seen = set()
        for ip in ips:
            if ip not in seen and not ip.startswith(("127.","192.","10.")):
                public_ips.append(ip)
                seen.add(ip)
        
        if not public_ips:
            log("❌ 区域内未发现任何 IP 字符串，请检查网页是否改版"); return
        
        log(f"🔎 成功识别 {len(public_ips)} 个潜在酒店 IP")

        # 4. 扫描前 6 个新 IP
        target_ips = [ip for ip in public_ips if ip not in history_ips][:MAX_IP_COUNT]
        if not target_ips:
            log("✅ 选定的 IP 均已在黑名单，跳过"); return

        for idx, ip in enumerate(target_ips, 1):
            log(f"\n[{idx}/{len(target_ips)}] 📡 探测: {ip}")
            found = False
            for port in PRIMARY_PORTS:
                sys.stdout.write(f"  ➜ {port} ")
                sys.stdout.flush()
                content = scan_ip_port(ip, port)
                if content:
                    sys.stdout.write("【✅】\n")
                    m = re.search(r'group-title="(.*?)"', content)
                    name = re.sub(r'[\\/:*?"<>|]', '', m.group(1).split()[-1]) if m else "酒店源"
                    with open(os.path.join(OUTPUT_DIR, f"{name}_{ip.replace('.','_')}_{port}.m3u"), "w", encoding="utf-8") as f:
                        f.write(content)
                    with open(HISTORY_FILE, "a") as h: h.write(f"{ip}:{port}\n")
                    found = True; break
                else:
                    sys.stdout.write("✕ "); sys.stdout.flush()
            if not found: sys.stdout.write("\n")
            time.sleep(2)

    except Exception as e: log(f"❌ 崩溃: {e}")

if __name__ == "__main__": main()
