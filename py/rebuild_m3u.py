import os
import json
import shutil
import re

HOTEL_DIR = "./hotel"
REBORN_DIR = "./reborn_list"
MAP_FILE = "py/scan_map.json"
MERGE_FILE = os.path.join(REBORN_DIR, "00_ALL_REBORN.m3u")

def rebuild():
    print("🧹 [动作] 正在强制清空历史输出目录...")
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

    # 处理每一条扫描结果
    for item in scan_results:
        old_h = item['old_host']
        new_h = item['new_host']
        
        # 寻找对应的模板
        for file in os.listdir(HOTEL_DIR):
            if file.endswith(".m3u") and not file.startswith("REBORN"):
                file_path = os.path.join(HOTEL_DIR, file)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                # 如果这个模板包含旧主机地址
                if old_h in content:
                    area_name = re.sub(r'_\d+.*', '', file.replace('.m3u', ''))
                    
                    # 1. 逐行处理内容，确保属性不丢失
                    new_lines = []
                    lines = content.split('\n')
                    for i in range(len(lines)):
                        line = lines[i].strip()
                        if not line: continue
                        
                        if line.startswith("#EXTINF"):
                            # A. 提取台标、ID等完整属性，仅修改 group-title
                            # 匹配 group-title="..." 的部分并替换
                            new_line = re.sub(r'group-title="[^"]+"', f'group-title="{area_name}_{new_h}"', line)
                            new_lines.append(new_line)
                            
                            # B. 处理下一行的 URL (执行 IP 替换)
                            if i + 1 < len(lines):
                                next_line = lines[i+1].strip()
                                if next_line.startswith("http"):
                                    replaced_url = next_line.replace(old_h, new_h)
                                    new_lines.append(replaced_url)
                                    
                                    # 将这一对 (信息+URL) 也加入大合集
                                    all_reborn_content.append(new_line)
                                    all_reborn_content.append(replaced_url)
                    
                    # 2. 生成单独的 M3U 文件
                    new_filename = f"REBORN_{area_name}_{new_h.replace('.', '_').replace(':', '_')}.m3u"
                    with open(os.path.join(REBORN_DIR, new_filename), "w", encoding="utf-8") as nf:
                        nf.write("#EXTM3U\n" + "\n".join(new_lines))
                    
                    print(f"  📝 已复活并拼接台标: {new_filename}")

    # 3. 写入整合大文件
    if len(all_reborn_content) > 1:
        with open(MERGE_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(all_reborn_content))
        print(f"\n🌟 [成功] 包含台标的合集已生成: {MERGE_FILE}")
    else:
        print("\n⚠️ [结束] 本次扫描未发现存活 IP。")

if __name__ == "__main__":
    rebuild()
