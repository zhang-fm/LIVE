import os, json, shutil, re

HOTEL_DIR = "./hotel"
REBORN_DIR = "./reborn_list"
MAP_FILE = "py/scan_map.json"
MERGE_FILE = os.path.join(REBORN_DIR, "00_ALL_REBORN.m3u")

def rebuild():
    # 🔥 第一步：强制清空目标文件夹，确保没有旧文件残留
    print(f"🧹 正在清空旧目录: {REBORN_DIR}")
    if os.path.exists(REBORN_DIR):
        shutil.rmtree(REBORN_DIR)
    os.makedirs(REBORN_DIR)

    if not os.path.exists(MAP_FILE):
        print("⚠️ 映射文件为空，跳过重建。")
        return

    with open(MAP_FILE, "r", encoding="utf-8") as f:
        scan_results = json.load(f)

    all_reborn_content = ["#EXTM3U"]

    # 第二步：根据最新扫描映射生成新文件
    for item in scan_results:
        old_h, new_h = item['old_host'], item['new_host']
        
        for file in os.listdir(HOTEL_DIR):
            if file.endswith(".m3u") and not file.startswith("REBORN"):
                with open(os.path.join(HOTEL_DIR, file), "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                if old_h in content:
                    # 替换为新 IP
                    new_content = content.replace(old_h, new_h)
                    # 提取干净的运营商名称
                    area_name = re.sub(r'_\d+.*', '', file.replace('.m3u', ''))
                    
                    new_filename = f"REBORN_{area_name}_{new_h.replace('.', '_').replace(':', '_')}.m3u"
                    
                    with open(os.path.join(REBORN_DIR, new_filename), "w", encoding="utf-8") as nf:
                        nf.write(new_content)
                    
                    # 提取频道并分类汇总
                    lines = new_content.split("\n")
                    for i in range(len(lines)):
                        if "#EXTINF" in lines[i]:
                            # 强制修改 group-title 方便在合集中区分来源
                            tag = re.sub(r'group-title="[^"]+"', f'group-title="{area_name}_{new_h}"', lines[i])
                            all_reborn_content.append(tag)
                            if i+1 < len(lines):
                                all_reborn_content.append(lines[i+1])

    # 第三步：生成唯一的整合大文件
    if len(all_reborn_content) > 1:
        with open(MERGE_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(all_reborn_content))
        print(f"🚀 大合集生成完毕，当前有效频道组：{len(scan_results)} 组")
    else:
        print("⚠️ 本次未发现任何有效频道。")

if __name__ == "__main__":
    rebuild()
