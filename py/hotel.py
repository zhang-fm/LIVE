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

# 酒店源高频端口优先
PRIMARY_PORTS = [8000, 8080, 9901, 8082, 8888, 9001, 8001, 8090, 9999, 888, 9003, 9888, 8081, 8181, 8899, 85, 808, 50001, 20443]

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
]

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

def manage_hotel_history():
    if datetime.now().weekday() == 0: 
        if os.path.exists(HISTORY_FILE):
            log("📅 周一清理酒店历史记录")
            os.remove(HISTORY_FILE)
    history_ips = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    history_ips.add(line.split(':')[0].strip())
    return history_ips

def save_history(ip, port):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{ip}:{port}\n")

def clean_name(name):
    if not name: return "酒店源"
    parts = name.split()
    last_part = parts[-1] if parts else name
    return re.sub(r'[\\/:*?"<>|]', '', last_part)

def scan_ip_port(ip, port):
    url = f"https://iptv.cqshushu.com/index.php?s={ip}:{port}&t=hotel&channels=1&download=m3u"
    try:
        time.sleep(random.uniform(1.2, 2.0))
        res = requests.get(url, headers={"User-Agent": random.choice(UA_LIST)}, timeout=TIMEOUT)
        if res.status_code == 200 and "#EXTINF" in res.text:
            return res.text
    except: pass
    return None

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    history_ips = manage_hotel_history()
    log(f"📜 已加载黑名单，包含 {len(history_ips)} 个 IP")
    
    if not os.path.exists(LOCAL_SOURCE):
        log(f"❌ 找不到源码文件: {LOCAL_SOURCE}")
        return

    try:
        with open(LOCAL_SOURCE, "r", encoding="utf-8") as f:
            html = f.read()
        
        # 1. 截取酒店区域
        if "Hotel IPTV" in html:
            hotel_section = html.split("Hotel IPTV")[1].split('class="group-section"')[0]
            log("🎯 已锁定酒店加密区域")
        else:
            hotel_section = html

        # 2. 解码加密的 IP (Base64)
        # 匹配长度16位以上的Base64字符串特征
        potential_b64 = re.findall(r'[A-Za-z0-9+/]{16,}={0,2}', hotel_section)
        decoded_ips = []
        for b in potential_b64:
            try:
                d = base64.b64decode(b).decode('utf-8')
                if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", d):
                    decoded_ips.append(d)
            except: continue
        
        # 3. 兜底抓取明文
        if not decoded_ips:
            decoded_ips = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", hotel_section)

        public_ips = []
        seen = set()
        for ip in decoded_ips:
            if ip not in seen and not ip.startswith(("127.", "192.", "10.")):
                public_ips.append(ip)
                seen.add(ip)

        if not public_ips:
            log("❌ 未发现有效 IP")
            return

        log(f"🔎 识别到 {len(public_ips)} 个酒店 IP")

        # 4. 开始扫描
        new_ips = [ip for ip in public_ips if ip not in history_ips][:MAX_IP_COUNT]
        if not new_ips:
            log("✅ 无需新探测")
            return

        for idx, ip in enumerate(new_ips, 1):
            log(f"\n[{idx}/{len(new_ips)}] 📡 探测: {ip}")
            found = False
            for port in PRIMARY_PORTS:
                sys.stdout.write(f"  ➜ {port} ")
                sys.stdout.flush()
                content = scan_ip_port(ip, port)
                if content:
                    sys.stdout.write("【✅】\n")
                    m = re.search(r'group-title="(.*?)"', content)
                    gname = clean_name(m.group(1)) if m else "酒店源"
                    fname = f"{gname}_{ip.replace('.', '_')}_{port}.m3u"
                    with open(os.path.join(OUTPUT_DIR, fname), "w", encoding="utf-8") as f:
                        f.write(content)
                    save_history(ip, port)
                    found = True
                    break
                else:
                    sys.stdout.write("✕ ")
                    sys.stdout.flush()
            if not found: sys.stdout.write("\n")
            time.sleep(3)

    except Exception as e:
        log(f"❌ 运行崩溃: {e}")

if __name__ == "__main__":
    main()
