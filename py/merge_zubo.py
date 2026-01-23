import os
import re

# ===============================
# 配置区
# ===============================
# 使用相对路径确保在 GitHub Actions 中稳健
BASE_DIR = os.getcwd()
INPUT_DIR = os.path.join(BASE_DIR, "zubo")
OUTPUT_FILE = os.path.join(INPUT_DIR, "zuboall.m3u")
LOGO_BASE_URL = "https://gcore.jsdelivr.net/gh/kenye201/TVlog/img"

def clean_group_title(line):
    """提取 [地名][运营商]"""
    match = re.search(r'group-title="(.*?)"', line)
    if match:
        full = match.group(1)
        isp_match = re.search(r'(电信|联通|移动|广电)', full)
        if isp_match:
            isp = isp_match.group(1)
            prefix = full[:full.find(isp)].strip()
            parts = prefix.split()
            simple_prefix = parts[-1] if parts else ""
            return re.sub(r'group-title=".*?"', f'group-title="{simple_prefix}{isp}"', line)
    return line

def fix_content(line):
    """修复台标、ID，并清洗频道显示名称"""
    if not line.startswith("#EXTINF"): return line
    name_match = re.search(r",([^,\n\r]+)$", line)
    if not name_match: return line
    
    raw_name = name_match.group(1).strip()
    display_name = re.sub(r'([-_\s]?(HD|高清|超清|SD))$', '', raw_name, flags=re.I).strip()
    line = line.replace(f",{raw_name}", f",{display_name}")
    
    clean = display_name.replace("-综合","").replace("综合","").replace(" ","").replace("中央","CCTV")
    cctv = re.search(r"(CCTV\d+)", clean, re.I)
    if cctv: clean = cctv.group(1).upper()
    
    logo = f'tvg-logo="{LOGO_BASE_URL}/{clean}.png"'
    tid = f'tvg-id="{display_name}"'
    
    line = re.sub(r'tvg-logo=".*?"', logo, line) if 'tvg-logo="' in line else line.replace("#EXTINF:-1", f"#EXTINF:-1 {logo}")
    line = re.sub(r'tvg-id=".*?"', tid, line) if 'tvg-id="' in line else line.replace("#EXTINF:-1", f"#EXTINF:-1 {tid}")
    
    return line

def main():
    all_channels = {}
    
    if not os.path.exists(INPUT_DIR):
        print(f"❌ 目录 {INPUT_DIR} 不存在，正在尝试创建...")
        os.makedirs(INPUT_DIR, exist_ok=True)
        return
    
    # 【核心修复点】：匹配 zubo_ 开头的文件，并排除 zuboall 自身
    files = [f for f in os.listdir(INPUT_DIR) 
             if f.endswith(".m3u") and f.startswith("zubo_") and f != "zuboall.m3u"]
    
    print(f"🔄 正在融合 {len(files)} 个文件...")
    
    for filename in files:
        file_path = os.path.join(INPUT_DIR, filename)
        # 增加大小检查，防止读取空文件
        if os.path.getsize(file_path) == 0:
            continue
            
        with open(file_path, "r", encoding="utf-8") as f:
            current_inf = ""
            for line in f:
                line = line.strip()
                if line.startswith("#EXTINF"):
                    line = clean_group_title(line)
                    current_inf = fix_content(line)
                elif line.startswith("http"):
                    if line not in all_channels:
                        all_channels[line] = current_inf
    
    if all_channels:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write('#EXTM3U x-tvg-url="https://fy.188766.xyz/e.xml" tvg-shift="0"\n')
            for url, inf in all_channels.items():
                f.write(f"{inf}\n{url}\n")
        print(f"✨ 融合完成！总计唯一频道数: {len(all_channels)}")
    else:
        print("⚠️ 未发现有效频道，跳过合并步骤")

if __name__ == "__main__":
    main()
