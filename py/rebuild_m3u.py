import os
import json
import shutil
import re

HOTEL_DIR = "./hotel"
REBORN_DIR = "./reborn_list"
MAP_FILE = "py/scan_map.json"
MERGE_FILE = os.path.join(REBORN_DIR, "00_ALL_REBORN.m3u")

def rebuild():
    # 1. 彻底清理并重建输出目录
    if os.path.exists(REBORN_DIR):
        shutil.rmtree(REBORN_DIR)
    os.makedirs(REBORN_DIR)

    if not os.path.exists(MAP_FILE): 
        print("❌ 映射文件不存在")
        return

    with open(MAP_FILE, "r", encoding="utf-8") as f:
        scan_results = json.load(f)

    all_reborn_content = ["#EXTM3U"]

    # 2. 遍历映射结果进行文件克隆
    for item in scan_results:
        old_h = item['old_host']
        new_h = item['new_host']
        
        for file in os.listdir(HOTEL_DIR):
            if file.endswith(".m3u") and not file.startswith("REBORN"):
                with open(os.path.join(HOTEL_DIR, file), "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                if old_h in content:
                    # 替换旧 IP 得到新内容
                    new_content = content.replace(old_h, new_h)
                    # 提取纯净名称 (例如：北京移动_223_72_123_57 -> 北京移动)
                    clean_name = re.sub(r'_\d+.*', '', file.replace('.m3u', ''))
                    
                    new_filename = f"REBORN_{clean_name}_{new_h.replace('.', '_').replace(':', '_')}.m3u"
                    
                    # 保存单个复活文件
                    with open(os.path.join(REBORN_DIR, new_filename), "w", encoding="utf-8") as nf:
                        nf.write(new_content)
                    
                    # 3. 提取频道到大合集
                    lines = new_content.split("\n")
                    for i in range(len(lines)):
                        if "#EXTINF" in lines[i]:
                            # 修改 group-title 为 运营商_新IP
                            tag = re.sub(r'group-title="[^"]+"', f'group-title="{clean_name}_{new_h}"', lines[i])
                            all_reborn_content.append(tag)
                            if i+1 < len(lines):
                                all_reborn_content.append(lines[i+1])

    # 4. 保存大合集
    with open(MERGE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(all_reborn_content))
    
    print(f"✅ 复活任务完成！新源已存放至 {REBORN_DIR}")

if __name__ == "__main__":
    rebuild()
