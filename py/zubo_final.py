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
OUTPUT_DIR = "zubo"
HISTORY_FILE = os.path.join(OUTPUT_DIR, "history.txt")
MAX_IP_COUNT = 6
TIMEOUT = 15

# 重新排序端口：根据目前组播源最常见的端口
PRIMARY_PORTS = [6636, 16888, 5002, 3333, 8188, 8055, 8288, 8880, 5555, 55555, 58888, 7000, 7700, 6003, 9988, 9999, 8012, 10000, 8888, 4022, 8188, 8022, 7777, 5146, 5140, 4056, 12320, 
    10000, 8080, 8000, 9901, 8090, 8181, 1234, 4000, 4001, 5148, 12345, 8805, 8187, 9926, 8222, 8808, 8883, 8686, 8188, 4023, 8848, 6666, 
    9000, 9001, 888, 9003, 8082, 20443, 85, 8081, 8001, 8003, 6001, 8899
]

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

def scan_ip_port(ip, port):
    url = f"https://iptv.cqshushu.com/index.php?s={ip}:{port}&t=multicast&channels=1&download=m3u"
    sys.stdout.write(f"  --> {port} ")
    sys.stdout.flush()

    try:
        time.sleep(random.uniform(3.0, 5.0))
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://iptv.cqshushu.com/"
        }
        res = requests.get(url, headers=headers, timeout=TIMEOUT)
        
        # --- 深度内容校验 ---
        text = res.text
        # 1. 基本特征检查
        is_m3u = "#EXTM3U" in text
        # 2. 排除伪装页面（比如“请稍候”、空列表、或只有头部没有频道的文件）
        # 真正的直播源文件通常至少包含几个 rtp:// 或 http:// 链接，且长度通常 > 500 字节
        has_content = text.count("rtp://") > 3 or text.count("http") > 3
        
        if res.status_code == 200 and is_m3u and has_content:
            sys.stdout.write("【✅ 真正成功】\n")
            return text
        elif "请稍候" in text or "检测中" in text:
            sys.stdout.write("【🛡️ 遇盾/跳转】")
        else:
            # 这里的 ✕ 代表虽然返回了 200，但里面是空壳或错误信息
            sys.stdout.write("✕ ")
    except:
        sys.stdout.write("⏰ ")
    
    sys.stdout.flush()
    return None

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    history_ips = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    history_ips.add(line.split(':')[0].strip())
    
    if not os.path.exists(LOCAL_SOURCE):
        log("❌ 找不到源码文件"); return

    try:
        with open(LOCAL_SOURCE, "r", encoding="utf-8") as f:
            content = f.read()

        # 精准提取 gotoIP 里的加密串
        b64_matches = re.findall(r"gotoIP\('([^']+)',\s*'multicast'\)", content)
        
        extracted_ips = []
        for b in b64_matches:
            try:
                # 补齐 base64 填充
                b += '=' * (-len(b) % 4)
                decoded_ip = base64.b64decode(b).decode('utf-8')
                if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", decoded_ip):
                    if decoded_ip not in extracted_ips:
                        extracted_ips.append(decoded_ip)
            except: continue

        target_ips = [ip for ip in extracted_ips if ip not in history_ips][:MAX_IP_COUNT]
        
        if not target_ips:
            log("🔎 暂无待测新目标。")
            return

        log(f"🎯 探测 {len(target_ips)} 个潜在组播目标 (严格校验模式)...")

        for idx, ip in enumerate(target_ips, 1):
            log(f"📡 [{idx}/{len(target_ips)}] 目标: {ip}")
            
            success_this_ip = False
            for port in PRIMARY_PORTS:
                file_content = scan_ip_port(ip, port)
                
                if file_content:
                    # 提取提供商
                    m = re.search(r'group-title="([^"]+)"', file_content)
                    tag = m.group(1).split()[-1] if m else "组播源"
                    
                    fn = f"{tag}_{ip.replace('.', '_')}_{port}.m3u"
                    with open(os.path.join(OUTPUT_DIR, fn), "w", encoding="utf-8") as f:
                        f.write(file_content)
                    
                    # 只有真正有内容才记入历史
                    with open(HISTORY_FILE, "a", encoding="utf-8") as hf:
                        hf.write(f"{ip}:{port}\n")
                    
                    success_this_ip = True
                    break 
            
            if not success_this_ip:
                print(f"\n❌ {ip} 未扫出有效内容。")
            
            time.sleep(3)

    except Exception as e:
        log(f"❌ 运行崩溃: {e}")

if __name__ == "__main__":
    main()
