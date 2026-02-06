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

def rebuild():
    print("Sweep 🧹 [动作] 正在强制清空历史输出目录...")
    if os.path.exists(REBORN_DIR):
        shutil.rmtree(REBORN_DIR)
        print(f"  🗑️  已删除旧文件夹: {REBORN_DIR}")
    os.makedirs(REBORN_DIR)
    print(f"  📂 已创建纯净目录: {REBORN_DIR}")

    if not os.path.exists(MAP_FILE):
        print("⚠️ 警告: 映射文件不存在，请先运行扫描脚本。")
        return

    with open(MAP_FILE, "r", encoding="utf-8") as f:
        scan_results = json.load(f)

    print(f"🔄 [动作] 开始根据 {len(scan_results)} 条最新记录重建 M3U...")
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
                            # --- 核心逻辑修改处 ---
                            
                            # 1. 提取频道标题 (通常在最后一个逗号之后)
                            title_match = re.search(r',([^,]+)$', line)
                            channel_title = title_match.group(1).strip() if title_match else "Unknown"
                            
                            # 2. 替换 group-title
                            temp_line = re.sub(r'group-title="[^"]+"', f'group-title="{area_name}_{new_h}"', line)
                            
                            # 3. 替换或插入 tvg-logo
                            # 如果原本有 tvg-logo="..." 则替换，如果没有则在逗号前插入
                            new_logo_attr = f'tvg-logo="{LOGO_BASE_URL}{channel_title}.png"'
                            if 'tvg-logo="' in temp_line:
                                new_line = re.sub(r'tvg-logo="[^"]+"', new_logo_attr, temp_line)
                            else:
                                # 在最后一个逗号前插入台标属性
                                new_line = temp_line.replace(f',{channel_title}', f' {new_logo_attr},{channel_title}')
                            
                            new_lines.append(new_line)
                            
                            # 4. 处理 URL 替换
                            if i + 1 < len(lines):
                                next_line = lines[i+1].strip()
                                if next_line.startswith("http"):
                                    replaced_url = next_line.replace(old_h, new_h)
                                    new_lines.append(replaced_url)
                                    
                                    # 同时加入合集
                                    all_reborn_content.append(new_line)
                                    all_reborn_content.append(replaced_url)
                    
                    # 生成文件
                    new_filename = f"REBORN_{area_name}_{new_h.replace('.', '_').replace(':', '_')}.m3u"
                    with open(os.path.join(REBORN_DIR, new_filename), "w", encoding="utf-8") as nf:
                        nf.write("#EXTM3U\n" + "\n".join(new_lines))
                    print(f"  📝 已复活并更新台标: {new_filename}")

    if len(all_reborn_content) > 1:
        with open(MERGE_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(all_reborn_content))
        print(f"\n🌟 [成功] 包含新台标的合集已生成: {MERGE_FILE}")
    else:
        print("\n⚠️ [结束] 本次扫描未发现存活 IP。")

if __name__ == "__main__":
    rebuild()
