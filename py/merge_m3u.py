import os
import re

INPUT_DIR = "test"
OUTPUT_FILE = "test/hotel_all.m3u"
LOGO_BASE_URL = "https://gcore.jsdelivr.net/gh/taksssss/tv/icon"

def clean_group_title(line):
    """提取 [地名][运营商]，例如: 广西联通"""
    match = re.search(r'group-title="(.*?)"', line)
    if match:
        full = match.group(1)
        isp_match = re.search(r'(电信|联通|移动|广电)', full)
        if isp_match:
            isp = isp_match.group(1)
            region = full[:2] # 取前两个字
            return re.sub(r'group-title=".*?"', f'group-title="{region}{isp}"', line)
    return line

def fix_content(line):
    """修复台标和 ID"""
    if not line.startswith("#EXTINF"): return line
    name_match = re.search(r",([^,\n\r]+)$", line)
    if not name_match: return line
    raw_name = name_match.group(1).strip()
    
    # 归一化频道名用于匹配台标 (CCTV1-综合HD -> CCTV1)
    clean = raw_name.replace("HD","").replace("高清","").replace("-综合","").replace("综合","").replace(" ","").replace("中央","CCTV")
    cctv = re.search(r"(CCTV\d+)", clean, re.I)
    if cctv: clean = cctv.group(1).upper()

    logo = f'tvg-logo="{LOGO_BASE_URL}/{clean}.png"'
    tid = f'tvg-id="{raw_name}"'
    
    line = re.sub(r'tvg-logo=".*?"', logo, line) if 'tvg-logo="' in line else line.replace("#EXTINF:-1", f"#EXTINF:-1 {logo}")
    line = re.sub(r'tvg-id=".*?"', tid, line) if 'tvg-id="' in line else line.replace("#EXTINF:-1", f"#EXTINF:-1 {tid}")
    return line

def main():
    all_channels = {} # 使用字典按 URL 去重
    
    if not os.path.exists(INPUT_DIR): return

    # 扫描 test 文件夹下所有的 m3u 文件
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".m3u") and f != "hotel_all.m3u"]
    print(f"🔄 正在融合 {len(files)} 个文件...")

    for filename in files:
        with open(os.path.join(INPUT_DIR, filename), "r", encoding="utf-8") as f:
            current_inf = ""
            for line in f:
                line = line.strip()
                if line.startswith("#EXTINF"):
                    line = clean_group_title(line)
                    current_inf = fix_content(line)
                elif line.startswith("http"):
                    # 如果 URL 已经存在，则不覆盖（保留先发现的那个，或者你可以根据需要调整）
                    if line not in all_channels:
                        all_channels[line] = current_inf

    # 写入最终的合集
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write('#EXTM3U x-tvg-url="https://fy.188766.xyz/e.xml"\n')
        for url, inf in all_channels.items():
            f.write(f"{inf}\n{url}\n")
    
    print(f"✨ 融合完成！总计唯一频道数: {len(all_channels)}")

if __name__ == "__main__":
    main()
