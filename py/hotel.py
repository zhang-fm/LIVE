import requests
import re
import os
import time

# ======================
# 基础配置
# ======================
HOME_URL = "https://iptv.cqshushu.com/"
OUTPUT_DIR = "test"
MERGED_FILE = "hotel_all.m3u"
MAX_IP_COUNT = 6
TIMEOUT = 6

# 台标基础地址 (taksssss 库)
LOGO_BASE_URL = "https://gcore.jsdelivr.net/gh/taksssss/tv/icon"

# 端口池
PRIMARY_PORTS = [8082, 9901, 8080, 8000, 9999, 8888, 8090, 8081, 8181, 8899, 8001, 85, 808]
SECONDARY_PORTS = [8088, 8001, 8899, 10000, 18080, 28080]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# ======================
# 核心功能函数
# ======================

def clean_channel_name(name):
    """
    清洗频道名称，用于匹配台标文件名
    """
    # 移除常见干扰词
    n = name.replace("HD", "").replace("高清", "").replace("-综合", "").replace("综合", "")
    n = n.replace("-", "").replace(" ", "").replace("超清", "").replace("中央", "CCTV")
    # 针对 CCTV 的特殊处理：将 "CCTV1综合" 变为 "CCTV1"
    match = re.search(r"(CCTV\d+)", n, re.I)
    if match:
        return match.group(1).upper()
    return n.strip()

def fix_m3u_line(line):
    """
    修复 #EXTINF 行中的 tvg-id 和 tvg-logo
    """
    if not line.startswith("#EXTINF"):
        return line

    # 提取频道显示名称（逗号后面的部分）
    name_match = re.search(r",([^,\n\r]+)$", line)
    if not name_match:
        return line
    
    raw_name = name_match.group(1).strip()
    clean_name = clean_channel_name(raw_name)

    # 构造标准属性
    # 修正原本失效的 logo 链接，改为 clean_name.png
    new_logo = f'tvg-logo="{LOGO_BASE_URL}/{clean_name}.png"'
    new_tvg_id = f'tvg-id="{raw_name}"'
    
    # 替换旧属性 (如果原本有 logo 就替换，没有就插入)
    if 'tvg-logo="' in line:
        line = re.sub(r'tvg-logo=".*?"', new_logo, line)
    else:
        line = line.replace("#EXTINF:-1", f"#EXTINF:-1 {new_logo}")
        
    if 'tvg-id="' in line:
        line = re.sub(r'tvg-id=".*?"', new_tvg_id, line)
    else:
        line = line.replace("#EXTINF:-1", f"#EXTINF:-1 {new_tvg_id}")

    return line

def fetch_homepage_ips():
    print("📥 获取首页最新 IP...")
    try:
        r = requests.get(HOME_URL, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        ips = []
        for ip in re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", r.text):
            if ip not in ips and not ip.startswith("127"):
                ips.append(ip)
            if len(ips) >= MAX_IP_COUNT:
                break
        print(f"✅ 成功提取 {len(ips)} 个 IP")
        return ips
    except Exception as e:
        print(f"❌ 访问首页失败: {e}")
        return []

def process_m3u_content(text):
    """
    处理下载到的 M3U 文本，修复每一行
    """
    lines = text.split('\n')
    processed_lines = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#EXTM3U"):
            continue
        if line.startswith("#EXTINF"):
            line = fix_m3u_line(line)
        processed_lines.append(line)
    return processed_lines

def try_download(ip, port):
    url = f"https://iptv.cqshushu.com/?s={ip}:{port}&t=hotel&channels=1&download=m3u"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200 and "#EXTINF" in r.text:
            content_list = process_m3u_content(r.text)
            return content_list, len(content_list) // 2
    except:
        pass
    return None, 0

# ======================
# 主程序
# ======================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ips = fetch_homepage_ips()
    if not ips: return

    # 合并文件的开头（带上 EPG 链接）
    all_merged_content = ['#EXTM3U x-tvg-url="https://fy.188766.xyz/e.xml"']
    seen_urls = set() # 用于去重，防止不同 IP 扫描到相同的频道流
    total_count = 0

    for ip in ips:
        print(f"\n🔍 扫描 IP: {ip}")
        found_in_ip = False
        for port in PRIMARY_PORTS + SECONDARY_PORTS:
            print(f"  ➜ 尝试端口 {port} ...", end=" ")
            lines, count = try_download(ip, port)

            if lines:
                print(f"✅ 命中 | 频道:{count}")
                # 加入合并列表，简单去重
                for i in range(0, len(lines), 2):
                    inf_line = lines[i]
                    url_line = lines[i+1] if i+1 < len(lines) else ""
                    if url_line and url_line not in seen_urls:
                        all_merged_content.append(inf_line)
                        all_merged_content.append(url_line)
                        seen_urls.add(url_line)
                        total_count += 1
                found_in_ip = True
                break 
            else:
                print("❌", end=" ")
            time.sleep(0.5)

    # 最终保存
    if total_count > 0:
        output_path = os.path.join(OUTPUT_DIR, MERGED_FILE)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(all_merged_content))
        print(f"\n✨ 任务完成！已修复台标并合并 {total_count} 个频道到 {output_path}")

if __name__ == "__main__":
    main()
