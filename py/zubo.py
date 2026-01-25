import requests
import re
import os
import base64

HOME_URL = "https://iptv.cqshushu.com/"
OUTPUT_DIR = "zubo"

def force_decode(text):
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

    # 模拟更像真实用户的 Headers
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Referer": "https://www.google.com/", # 伪装从搜索结果进入
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    print("🛰️ 正在尝试深度绕过探测...")
    try:
        session = requests.Session()
        res = session.get(HOME_URL, headers=headers, timeout=15)
        res.encoding = 'utf-8'
        html = res.text
        
        # 调试输出：打印源码片段，确认是否被防火墙拦截
        print(f"📄 页面快照 (前150字): {html[:150].strip()}...")

        # 1. 尝试从 gotoIP 提取
        # 2. 尝试从 data- 属性提取
        # 3. 尝试扫描所有引号内的内容
        found_ips = set()
        
        # 专门匹配 gotoIP('xxx')
        goto_matches = re.findall(r"gotoIP\(['\"]([^'\"]+)['\"]", html)
        # 专门匹配 data-ip="xxx"
        data_matches = re.findall(r"data-[^=]+=[\"']([A-Za-z0-9+/=]{8,})[\"']", html)
        # 广谱匹配
        all_strings = re.findall(r"['\"]([A-Za-z0-9+/=]{8,})['\"]", html)

        for item in (goto_matches + data_matches + all_strings):
            ip = force_decode(item)
            if ip:
                found_ips.add(ip)

        print(f"📍 提取到的 IP 列表: {list(found_ips)}")

        if not found_ips:
            print("⚠️ 依然没找到 IP。可能需要检查 '页面快照' 是否显示了 'Access Denied' 或验证码。")
            return

        count = 0
        ports = ['8001', '8000', '4022', '16888']
        for ip in found_ips:
            for port in ports:
                # 注意：网站可能会根据 Cookie 校验下载权限，这里复用 session
                test_url = f"{HOME_URL}download.php?s={ip}:{port}&t=mcast"
                try:
                    m3u_res = session.get(test_url, headers=headers, timeout=8)
                    if "#EXTINF" in m3u_res.text:
                        with open(f"{OUTPUT_DIR}/{ip.replace('.', '_')}_{port}.m3u", "w", encoding="utf-8") as f:
                            f.write(m3u_res.text)
                        print(f"✅ 成功抓取: {ip}:{port}")
                        count += 1
                        break 
                except:
                    continue
        
        print(f"🏁 任务完成，成功获取 {count} 个文件。")

    except Exception as e:
        print(f"❌ 运行报错: {e}")

if __name__ == "__main__":
    main()
