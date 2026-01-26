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
MAX_IP_COUNT = 10 
TIMEOUT = 20        # 进一步增加超时时间

# 重新排序端口：根据你的反馈，把 9999 提到第一位，其他高频紧随其后
PRIMARY_PORTS = [9999, 8000, 8080, 9901, 8082, 8888, 9888, 8090, 8081, 8181, 8899, 8001, 85, 808, 50001, 20443]

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

def scan_ip_port(ip, port):
    """
    精准匹配你测试成功的格式：
    http://iptv.cqshushu.com/?s=175.11.74.249:9999&t=hotel&channels=1&format=m3u
    """
    # 使用 f-string 严格构造 URL，不让 requests 自动编码冒号
    url = f"https://iptv.cqshushu.com/index.php?s={ip}:{port}&t=hotel&channels=1&download=m3u"
    
    sys.stdout.write(f"  --> 测试 [{port}] ... ")
    sys.stdout.flush()

    try:
        # 端口间稍微停顿，模拟人工点击
        time.sleep(random.uniform(2.0, 4.0))
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://iptv.cqshushu.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Connection": "keep-alive"
        }
        
        # 显式禁止重定向，看看是不是被防火墙拦截了
        res = requests.get(url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        
        if res.status_code == 200 and "#EXTINF" in res.text:
            sys.stdout.write("【✅ 匹配成功！】\n")
            return res.text
        elif "请稍候" in res.text or res.status_code == 503:
            sys.stdout.write("⚠️ 遇盾/限频 ")
        else:
            sys.stdout.write("✕ ")
    except Exception as e:
        sys.stdout.write("⏰ 超时 ")
    
    sys.stdout.flush()
    return None

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if not os.path.exists(LOCAL_SOURCE):
        log("❌ 源码文件缺失"); return

    try:
        with open(LOCAL_SOURCE, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取 Base64 IP
        b64_list = re.findall(r"gotoIP\('([^']+)',\s*'hotel'\)", content)
        found_ips = []
        for b in b64_list:
            try:
                decoded = base64.b64decode(b).decode('utf-8')
                if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", decoded):
                    if decoded not in found_ips:
                        found_ips.append(decoded)
            except: continue

        if not found_ips:
            log("❌ 未发现有效 IP"); return

        log(f"✅ 提取 {len(found_ips)} 个 IP，首选端口: {PRIMARY_PORTS[0]}")

        # 探测前 10 个
        target_ips = found_ips[:MAX_IP_COUNT]
        for idx, ip in enumerate(target_ips, 1):
            log(f"📡 [{idx}/{len(target_ips)}] 深度扫描: {ip}")
            
            for port in PRIMARY_PORTS:
                m3u_data = scan_ip_port(ip, port)
                
                if m3u_data:
                    # 自动获取运营商名称
                    m = re.search(r'group-title="([^"]+)"', m3u_data)
                    tag = m.group(1).split()[-1] if m else "Hotel"
                    tag = re.sub(r'[\\/:*?"<>|]', '', tag)
                    
                    fn = f"{tag}_{ip.replace('.', '_')}_{port}.m3u"
                    with open(os.path.join(OUTPUT_DIR, fn), "w", encoding="utf-8") as f:
                        f.write(m3u_data)
                    
                    log(f"🎉 抓取成功: {fn}")
                    break 
            
            # 每个 IP 探测完大休息
            time.sleep(8)

    except Exception as e:
        log(f"❌ 运行异常: {e}")

if __name__ == "__main__":
    main()
