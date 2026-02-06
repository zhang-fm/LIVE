import os
import json
import shutil
import re

HOTEL_DIR = "./hotel"
REBORN_DIR = "./reborn_list"
MAP_FILE = "py/scan_map.json"
MERGE_FILE = os.path.join(REBORN_DIR, "00_ALL_REBORN.m3u")
LOGO_BASE_URL = "https://tb.yubo.qzz.io/logo/"

def rebuild():
    # 1. 物理清理旧文件夹
    if os.path.exists(REBORN_DIR):
        shutil.rmtree(REBORN_DIR)
    os.makedirs(REBORN_DIR)

    if not os.path.exists(MAP_FILE): 
        print("❌ 映射文件不存在")
        return

    with open(MAP_FILE, "r", encoding="utf-8") as f:
        scan_results = json.load(f)

    all_reborn_content = ['#EXTM3U x-tvg-url="https://fy.188766.xyz/e.xml"']

    # 2. 遍历映射结果
    for item in scan_results:
        old_h = item['old_host']
        new_h = item['new_host']
        
        for file in os.listdir(HOTEL_DIR):
            if file.endswith(".m3u") and not file.startswith("REBORN"):
                file_path = os.path.join(HOTEL_DIR, file)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                if old_h in content:
                    # 获取纯净名称 (北京移动_223_72_123_57 -> 北京移动)
                    clean_name = re.sub(r'_\d+.*', '', file.replace('.m3u', ''))
                    
                    # 3. 按行处理，修复台标和链接
                    lines = content.split("\n")
                    new_file_lines = ['#EXTM3U x-tvg-url="https://fy.188766.xyz/e.xml"']
                    
                    for i in range(len(lines)):
                        line = lines[i].strip()
                        if line.startswith("#EXTINF"):
                            # A. 提取频道名称 (逗号后面的部分)
                            tv_name = line.split(',')[-1].strip()
                            
                            # B. 构造新台标链接
                            new_logo = f"{LOGO_BASE_URL}{tv_name}.png"
                            
                            # C. 替换原有台标 (正则匹配 tvg-logo="...")
                            line = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{new_logo}"', line)
                            
                            # D. 替换 group-title (运营商_IP)
                            line = re.sub(r'group-title="[^"]+"', f'group-title="{clean_name}_{new_h}"', line)
                            
                            # E. 保存修改后的标签行
                            new_file_lines.append(line)
                            
                            # F. 处理下一行链接
                            if i + 1 < len(lines):
                                next_line = lines[i+1].strip()
                                if next_line.startswith("http"):
                                    # 替换 IP 和 端口
                                    final_url = next_line.replace(old_h, new_h)
                                    new_file_lines.append(final_url)
                                    
                                    # 同时存入合集
                                    all_reborn_content.append(line)
                                    all_reborn_content.append(final_url)

                    # 4. 保存单个复活文件
                    new_filename = f"REBORN_{clean_name}_{new_h.replace('.', '_').replace(':', '_')}.m3u"
                    with open(os.path.join(REBORN_DIR, new_filename), "w", encoding="utf-8") as nf:
                        nf.write("\n".join(new_file_lines))

    # 5. 保存大合集
    with open(MERGE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(all_reborn_content))
    
    print(f"✅ 台标修复版复活任务完成！存放在 {REBORN_DIR}")

if __name__ == "__main__":
    rebuild()
