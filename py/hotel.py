import requests
import re
import os
import time
import base64
import random

# ======================
# 深度配置区
# ======================
HOME_URL = "https://iptv.cqshushu.com/"
OUTPUT_DIR = "test"
MAX_IP_COUNT = 8  # 稍微增加一点目标，因为我们现在有了更精准的手段
TIMEOUT = 12 

# 常用酒店端口
PRIMARY_PORTS = [8082, 9901, 888, 9003, 8080, 8000, 9999, 8888, 8090, 8081, 8181, 8899, 8001, 85, 808, 20443]

# 随机 User-Agent 库，模拟不同用户环境
UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
]

def get_headers():
    return {
        "User-Agent": random.choice(UA_LIST),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Referer": "https://fofa.info/",
        "Connection": "keep-alive"
    }

def get_fofa_ports(ip):
    """带高度随机延时的 FOFA 探测逻辑"""
    # 随机休眠 5 到 12 秒，模拟人类在网页点击的间隔
    sleep_time = random.uniform(5, 12)
    print(f"   ⏳ FOFA 冷却中 ({sleep_time:.1f}s)... ", end="", flush=True)
    time.sleep(sleep_time)

    try:
        query = base64.b64encode(ip.encode()).decode()
        search_url = f"https://fofa.info/result?qbase64={query}"
        
        res = requests.get(search_url, headers=get_headers(), timeout=15)
        
        if "验证码" in res.text or "429 Too Many Requests" in res.text:
            print("❌ 被拦截")
            return None # 触发风控
        
        # 提取端口：匹配 1.2.3.4:8080 这种格式
        found_ports = re.findall(rf'{ip}:(\d+)', res.text)
        ports = list(set([int(p) for p in found_ports]))
        print(f"✅ 探测到端口: {ports}")
        return ports
    except Exception as e:
        print(f"❌ 出错: {e}")
        return []

def scan_ip_port(ip, port):
    """执行最终的 m3u 抓取"""
    url = f"https://iptv.cqshushu.com/?s={ip}:{port}&t=hotel&channels=1&download=m3u"
    try:
        # 为了不给目标服务器太大压力，这里也做微小延时
        time.sleep(random.uniform(1.5, 3))
        res = requests.get(url, headers=get_headers(), timeout=TIMEOUT)
        if res.status_code == 200 and "#EXTINF" in res.text:
            return res.text
    except:
        pass
    return None

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"🚀 启动慢速精准抓取任务... (目标: {MAX_IP_COUNT}个IP)")
    
    # 1. 获取目标 IP 列表
    try:
        r = requests.get(HOME_URL, headers=get_headers(), timeout=TIMEOUT)
        r.raise_for_status()
        ips = []
        for ip in re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", r.text):
            if ip not in ips and not ip.startswith("127"):
                ips.append(ip)
        ips = ips[:MAX_IP_COUNT]
        print(f"📍 首页获取到 {len(ips)} 个待处理 IP")
    except Exception as e:
        print(f"❌ 首页访问失败: {e}")
        return

    # 2. 逐个 IP 处理
    fofa_blocked = False
    for idx, ip in enumerate(ips, 1):
        print(f"\n[{idx}/{len(ips)}] 📡 正在处理: {ip}")
        
        ports_to_test = []
        
        # 优先使用 FOFA，除非已被封锁
        if not fofa_blocked:
            f_ports = get_fofa_ports(ip)
            if f_ports is None:
                fofa_blocked = True
                print("   ⚠️ FOFA 访问受限，后续 IP 将全量使用穷举模式。")
                ports_to_test = PRIMARY_PORTS
            else:
                # 组合端口：FOFA 发现的排在最前面
                ports_to_test = f_ports + [p for p in PRIMARY_PORTS if p not in f_ports]
        else:
            ports_to_test = PRIMARY_PORTS

        # 执行端口扫描
        found_success = False
        for port in ports_to_test:
            print(f"   ➜ 测试端口 {port} ... ", end="", flush=True)
            content = scan_ip_port(ip, port)
            
            if content:
                filename = f"raw_{ip}_{port}.m3u"
                with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
                    f.write(content)
                print("✅ 抓取成功！")
                found_success = True
                break # 只要一个端口成功，就跳过该 IP 剩余端口
            else:
                print("✕")
        
        if not found_success:
            print(f"   ⚠️ IP {ip} 扫描完毕，未获取到有效数据。")
            
        # 每个 IP 扫完后，额外休眠一段时间，防止 GitHub IP 被 cqshushu 封锁
        extra_sleep = random.uniform(3, 8)
        print(f"💤 IP 间隔休眠 {extra_sleep:.1f}s...")
        time.sleep(extra_sleep)

if __name__ == "__main__":
    main()
