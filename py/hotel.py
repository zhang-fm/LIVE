import requests
import re
import os
import time

# ======================
# 基础配置
# ======================
HOME_URL = "https://iptv.cqshushu.com/"
OUTPUT_DIR = "test"
MERGED_FILE = "hotel_all.m3u"  # 最终合并后的文件名
MAX_IP_COUNT = 6
TIMEOUT = 6

PRIMARY_PORTS = [8082, 9901, 8080, 8000, 9999, 8888, 8090, 8081, 8181, 8899, 8001, 85, 808]
SECONDARY_PORTS = [8088, 8001, 8899, 10000, 18080, 28080]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def fetch_homepage_ips():
    print("📥 获取首页 IP...")
    try:
        r = requests.get(HOME_URL, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        ips = []
        for ip in re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", r.text):
            if ip not in ips:
                ips.append(ip)
            if len(ips) >= MAX_IP_COUNT:
                break
        print(f"共加载 {len(ips)} 个 IP")
        return ips
    except Exception as e:
        print(f"❌ 获取 IP 失败: {e}")
        return []

def try_download(ip, port):
    url = f"https://iptv.cqshushu.com/?s={ip}:{port}&t=hotel&channels=1&download=m3u"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200 and "#EXTM3U" in r.text:
            # 提取 #EXTINF 之后的内容（去掉第一行的 #EXTM3U）
            lines = r.text.split('\n')
            content_lines = [line for line in lines if line.strip() and not line.startswith("#EXTM3U")]
            channels = r.text.count("#EXTINF")
            return content_lines, channels
    except:
        pass
    return None, 0

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ips = fetch_homepage_ips()
    if not ips: return

    all_merged_content = ["#EXTM3U"] # 初始化合并列表，带上文件头
    total_channels = 0

    for ip in ips:
        print(f"\n🔍 扫描 IP: {ip}")
        found = False
        for port in PRIMARY_PORTS + SECONDARY_PORTS:
            print(f"  ➜ 尝试端口 {port} ...", end=" ")
            content_lines, channels = try_download(ip, port)

            if content_lines:
                print(f"✅ 命中 | 频道:{channels}")
                all_merged_content.extend(content_lines) # 将频道内容加入大列表
                total_channels += channels
                found = True
                break # 命中一个 IP 的一个端口就跳过，避免内容重复过多
            else:
                print("❌", end=" ")
            time.sleep(1)

        if not found:
            print("\n  ⛔ 本 IP 未发现有效端口")

    # 保存合并后的文件
    if total_channels > 0:
        output_path = os.path.join(OUTPUT_DIR, MERGED_FILE)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(all_merged_content))
        print(f"\n✨ 任务完成！总计合并 {total_channels} 个频道")
        print(f"💾 文件保存在: {output_path}")

if __name__ == "__main__":
    main()
