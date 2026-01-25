import requests
import re
import os
import base64

HOME_URL = "https://iptv.cqshushu.com/"
OUTPUT_DIR = "zubo"

def decode_base64(data):
    """尝试解码 Base64，验证是否为合法的 IP 格式"""
    try:
        # 补齐 Base64 填充
        missing_padding = len(data) % 4
        if missing_padding:
            data += '=' * (4 - missing_padding)
        decoded = base64.b64decode(data).decode('utf-8')
        # 正则验证是否为 IP 格式 (x.x.x.x)
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", decoded):
            return decoded
    except:
        pass
    return None

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🚀 开始请求页面...")
    try:
        res = requests.get(HOME_URL, headers=headers, timeout=15)
        res.encoding = 'utf-8'
        html = res.text

        # 方案 A: 匹配 gotoIP('...', '...')
        found_ips = set()
        matches = re.findall(r"['\"]([A-Za-z0-9+/=]{8,})['\"]", html)
        
        for item in matches:
            ip = decode_base64(item)
            if ip:
                found_ips.add(ip)

        print(f"📍 发现有效 IP: {list(found_ips)}")

        count = 0
        ports = [
    6636, 16888, 5002, 3333, 8188, 8055, 8288, 8880, 5555, 55555, 58888, 7000, 7700, 6003, 9988, 9999, 8012, 10000, 8888, 4022, 8188, 8022, 7777, 5146, 5140, 4056, 12320, 
    10000, 8080, 8000, 9901, 8090, 8181, 1234, 4000, 4001, 5148, 12345, 8805, 8187, 9926, 8222, 8808, 8883, 8686, 8188, 4023, 8848, 6666, 
    9000, 9001, 888, 9003, 8082, 20443, 85, 8081, 8001, 8003, 6001, 8899
]
        
        for ip in found_ips:
            for port in ports:
                # 构造下载 m3u 的接口地址
                # 注意：如果网站接口变了，这里可能需要根据 F12 网络面板重新调整
                download_url = f"{HOME_URL}download.php?s={ip}:{port}&t=mcast" 
                
                try:
                    m3u_res = requests.get(download_url, headers=headers, timeout=5)
                    if "#EXTINF" in m3u_res.text:
                        with open(f"{OUTPUT_DIR}/{ip}_{port}.m3u", "w", encoding="utf-8") as f:
                            f.write(m3u_res.text)
                        count += 1
                        break
                except:
                    continue
        
        print(f"✅ 完成！共保存 {count} 个文件。")

    except Exception as e:
        print(f"❌ 运行异常: {e}")

if __name__ == "__main__":
    main()
