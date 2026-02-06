import os
import json
import shutil
import re

HOTEL_DIR = "./hotel"
REBORN_DIR = "./reborn_list"
MAP_FILE = "py/scan_map.json"
MERGE_FILE = os.path.join(REBORN_DIR, "00_ALL_REBORN.m3u")
# 新的台标前缀
LOGO_BASE_URL = "https://tb.yubo.qzz.io/logo/"

def clean_channel_name(name):
    """
    清洗频道名称：剔除画质词汇，标准化央视命名
    """
    # 1. 统一转大写，处理画质词清洗
    # 清洗：高清, 标清, 普清, 超清, HD, SD, (HD), [HD], -HD 等
    name = re.sub(r'(高清|标清|普清|超清|超高清|H\.265|4K|HD|SD|hd|sd)', '', name, flags=re.I)
    # 移除括号及多余空格
    name = re.sub(r'[\(\)\[\]\-\s]+', '', name)
    
    # 2. 央视标准化洗版 (CCTV1-CCTV17)
    # 匹配类似 CCTV1, cctv-1, CCTV 1, CCTV5+, CCTV-5+ 等
    cctv_match = re.search(r'CCTV[- ]?(\d+)(\+)?', name, re.I)
    if cctv_match:
        num = cctv_match.group(1)
        plus = "+" if cctv_match.group(2) else ""
        # 强制格式化为 CCTV-X
        name = f"CCTV-{num}{plus}"
    
    return name.strip()

def rebuild():
    print("🧹 [动作] 正在强制清空历史输出目录...")
    if os.path.exists(REBORN_DIR):
        shutil.rmtree(REBORN_DIR)
    os.makedirs(REBORN_DIR)

    if not os.path.exists(MAP_FILE):
        print("⚠️ 警告: 映射文件不存在，请先运行扫描脚本。")
        return

    with open(MAP_FILE, "r", encoding="utf-8") as f:
        scan_results = json.load(f)

    print(f"🔄 [动作] 开始根据 {len(scan_results)} 条记录重建 M3U 并执行洗版...")
    all_reborn_content = ["#EXTM3U"]

    for item in scan_results:
        old_h = item['old_host']
        new_h = item['new_host']
        
        for file in os.listdir(HOTEL_DIR):
            if file.endswith(".m3u") and not file.startswith("REBORN"):
                file_path = os.path.join(HOTEL_DIR, file)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                if old_h in content:
                    area_name = re.sub(r'_\d+.*', '', file.replace('.m3u', ''))
                    new_lines = []
                    lines = content.split('\n')
                    
                    for i in range(len(lines)):
                        line = lines[i].strip()
                        if not line: continue
                        
                        if line.startswith("#EXTINF"):
                            # 1. 提取原始频道名
                            title_match = re.search(r',([^,]+)$', line)
                            raw_title = title_match.group(1).strip() if title_match else "Unknown"
                            
                            # 2. 【核心洗版】清洗频道名
                            clean_title = clean_channel_name(raw_title)
                            
                            # 3. 替换 group-title
                            temp_line = re.sub(r'group-title="[^"]+"', f'group-title="{area_name}_{new_h}"', line)
                            
                            # 4. 更新 tvg-name 和 tvg-logo
                            # 统一 tvg-name 为清洗后的名称
                            if 'tvg-name="' in temp_line:
                                temp_line = re.sub(r'tvg-name="[^"]+"', f'tvg-name="{clean_title}"', temp_line)
                            
                            # 更新 tvg-logo
                            new_logo_attr = f'tvg-logo="{LOGO_BASE_URL}{clean_title}.png"'
                            if 'tvg-logo="' in temp_line:
                                temp_line = re.sub(r'tvg-logo="[^"]+"', new_logo_attr, temp_line)
                            else:
                                temp_line = temp_line.replace(f',{raw_title}', f' {new_logo_attr},{raw_title}')
                            
                            # 5. 替换行末显示的名称（洗版最终呈现效果）
                            new_line = temp_line.replace(f',{raw_title}', f',{clean_title}')
                            new_lines.append(new_line)
                            
                            # 6. 处理 URL 替换
                            if i + 1 < len(lines):
                                next_line = lines[i+1].strip()
                                if next_line.startswith("http"):
                                    replaced_url = next_line.replace(old_h, new_h)
                                    new_lines.append(replaced_url)
                                    all_reborn_content.append(new_line)
                                    all_reborn_content.append(replaced_url)
                    
                    new_filename = f"REBORN_{area_name}_{new_h.replace('.', '_').replace(':', '_')}.m3u"
                    with open(os.path.join(REBORN_DIR, new_filename), "w", encoding="utf-8") as nf:
                        nf.write("#EXTM3U\n" + "\n".join(new_lines))
                    print(f"  📝 已洗版并输出: {new_filename}")

    if len(all_reborn_content) > 1:
        with open(MERGE_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(all_reborn_content))
        print(f"\n🌟 [成功] 标准化台标合集已生成: {MERGE_FILE}")

if __name__ == "__main__":
    rebuild()
