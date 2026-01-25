import requests
import re
import os
import base64

HOME_URL = "https://iptv.cqshushu.com/"
OUTPUT_DIR = "zubo"

def force_decode(text):
    """强制尝试从一串杂乱文本中提取 Base64 IP"""
    # 匹配可能的 Base64 特征字符（8位以上）
    candidates = re.findall(r'[A-Za-z0-9+/]{8,12}={0,2}', text)
    for c in candidates:
        try:
            missing_padding = len(c) % 4
            if missing_padding:
                c += '=' * (4 - missing_padding)
            decoded = base64.b64decode(c).decode('utf-8')
            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", decoded):
                return decoded
        except:
            continue
    return None

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": HOME_URL
    }

    print("🚀 正在深度扫描页面源码...")
    try:
        res = requests.get(HOME_URL, headers=headers, timeout=15)
        res.encoding = 'utf-8'
        html = res.text
        
        # 提取所有可能包含 Base64 的标签内容
        # 比如 onclick="gotoIP('XXXX', 'mcast')" 或 data-ip="XXXX"
        potential_blocks = re.findall(r"['\"]([A-Za-z0-9+/=]{8,})['\"]", html)
        
        found_ips = set()
        for block in potential_blocks:
            ip = force_decode(block)
            if ip:
                found_ips.add(ip)
        
        # 如果还是没找到，尝试直接找页面里是否有明文 IP (备选)
        if not found_ips:
            raw_ips = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", html)
            for ip in raw_ips:
                if not ip.startswith("127."):
                    found_ips.add(ip)

        print(f"📍 提取到的 IP 列表: {list(found_ips)}")

        if not found_ips:
            print("❌ 依然未发现有效 IP。可能是网站加了人机验证或动态混淆。")
            return

        count = 0
        # 尝试常用组播转单播端口
        ports = ['8001', '8000', '4022', '16888']
        
        for ip in found_ips:
            for port in ports:
                # 构造下载链接
                test_url = f"{HOME_URL}download.php?s={ip}:{port}&t=mcast"
                try:
                    m3u_res = requests.get(test_url, headers=headers, timeout=8)
                    if "#EXTINF" in m3u_res.text:
                        with open(f"{OUTPUT_DIR}/{ip.replace('.', '_')}_{port}.m3u", "w", encoding="utf-8") as f:
                            f.write(m3u_res.text)
                        print(f"✅ 成功提取: {ip}:{port}")
                        count += 1
                        break 
                except:
                    continue
        
        print(f"🏁 任务完成，保存了 {count} 个文件。")

    except Exception as e:
        print(f"❌ 运行报错: {e}")

if __name__ == "__main__":
    main()
