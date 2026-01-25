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
MAX_IP_COUNT = 6  # 首页 IP 较多，建议多扫一点
TIMEOUT = 12

PRIMARY_MULTICAST_PORTS = [
    8001, 8000, 4022, 16888, 5002, 3333, 8188, 8055, 8288, 8880, 5555, 7000, 9999, 10000, 8888, 8080
]

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
]

def extract_provider_from_m3u(m3u_text):
    """从 M3U 内容中提取 group-title 里的运营商信息"""
    try:
        # 寻找 group-title="... 上海电信"
        match = re.search(r'group-title="([^"]+)"', m3u_text)
        if match:
            group_info = match.group(1).replace("组播", "").strip()
            # 提取最后一段，通常是 "上海电信"
            return group_info.split()[-1] if " " in group_info else group_info
    except: pass
    return "未知运营商"

def manage_history():
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    if datetime.now().weekday() == 0 and os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    
    history_ips = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                ip = line.split(':')[0].strip()
                if ip: history_ips.add(ip)
    return history_ips

def get_headers():
    return {"User-Agent": random.choice(UA_LIST), "Referer": HOME_URL}

def get_fofa_ports(ip):
    # 稍微缩短延时，提高效率
    time.sleep(random.uniform(2, 4))
    try:
        query = base64.b64encode(ip.encode()).decode()
        res = requests.get(f"https://fofa.info/result?qbase64={query}", headers=get_headers(), timeout=15)
        # 匹配任何出现在该 IP 后面的端口
        ports = re.findall(rf'{re.escape(ip)}:(\d+)', res.text)
        return sorted(list(set([int(p) for p in ports if int(p) > 80])))
    except: return []

def scan_ip_port(ip, port):
    url = f"https://iptv.cqshushu.com/?s={ip}:{port}&t=multicast&channels=1&download=m3u"
    try:
        res = requests.get(url, headers=get_headers(), timeout=TIMEOUT)
        if res.status_code == 200 and "#EXTINF" in res.text:
            return res.text
    except: pass
    return None

def main():
    history_ips = manage_history()
    print(f"🚀 启动组播源抓取任务...")
    
    try:
        r = requests.get(HOME_URL, headers=get_headers(), timeout=TIMEOUT)
        # 增强版正则：排除内网 IP，并抓取 HTML 标签内的 IP
        found_ips = re.findall(r'(?:[1-9]\d{0,2}\.){3}[1-9]\d{0,2}', r.text)
        
        # 过滤和去重
        target_ips = []
        for ip in found_ips:
            if ip.startswith(("127.", "192.", "10.", "172.")): continue
            if ip not in target_ips and ip not in history_ips:
                target_ips.append(ip)
        
        # 只取最新的部分进行探测
        target_ips = target_ips[:MAX_IP_COUNT]
        print(f"📍 首页获取到 {len(target_ips)} 个待测 IP 目标")
        
    except Exception as e:
        print(f"❌ 首页访问失败: {e}"); return

    if not target_ips:
        print("💡 暂无新 IP 需要探测（或首页未抓取到 IP）。")
        return

    for idx, ip in enumerate(target_ips, 1):
        print(f"\n[{idx}/{len(target_ips)}] 📡 探测中: {ip}")
        f_ports = get_fofa_ports(ip)
        # 优先测 FOFA 发现的端口，再测常用端口
        test_ports = f_ports + [p for p in PRIMARY_MULTICAST_PORTS if p not in f_ports]
        
        found_ok = False
        for port in test_ports:
            print(f"  ➜ {port} ", end="", flush=True)
            content = scan_ip_port(ip, port)
            if content:
                # 提取命名
                provider = extract_provider_from_m3u(content)
                filename = f"{provider}-{ip.replace('.', '_')}.m3u"
                
                with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
                    f.write(content)
                
                # 写入历史记录
                with open(HISTORY_FILE, "a") as f_h: f_h.write(f"{ip}:{port}\n")
                
                print(f" ✅ 成功: {filename}")
                found_ok = True
                break
            else:
                print("✕ ", end="")
        
        time.sleep(random.uniform(1, 3))

if __name__ == "__main__":
    main()
