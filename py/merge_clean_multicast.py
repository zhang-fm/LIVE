import os
import re
from collections import OrderedDict

# 配置
INPUT_DIR = "test_multicast"                  # 输入目录
OUTPUT_FILE = "clean_all_multicast.m3u"       # 输出大文件
HEADER = '#EXTM3U x-tvg-url="https://fy.188766.xyz/e.xml" tvg-shift="0"'

# 运营商关键词（用于提取简化 group-title）
OPERATORS = ["电信", "联通", "移动"]

def simplify_group(group):
    """简化 group-title，只保留运营商+地名（如 北京联通、广东电信）"""
    if not group:
        return "其他"
    
    # 提取最后一个运营商关键词 + 前面的地名
    for op in OPERATORS:
        if op in group:
            # 取运营商前面的部分 + 运营商
            idx = group.rfind(op)
            prefix = group[:idx].strip()
            # 只保留最后一个地名（去掉多余的省市区）
            parts = prefix.split()
            simple_prefix = parts[-1] if parts else ""
            return f"{simple_prefix}{op}"
    
    return group  # 没匹配到运营商就原样返回

def extract_channel_name(info_line):
    """从 #EXTINF 提取纯频道名（如 CCTV3、湖南卫视）"""
    # 去掉前面的 #EXTINF:...,
    match = re.search(r',(.+)$', info_line)
    if match:
        name = match.group(1).strip()
        # 进一步清理（去掉 HD/4K 等后缀，如果需要）
        name = re.sub(r'\s*(HD|4K|超高清|高清|\+|\s*)$', '', name, flags=re.I).strip()
        return name
    return "未知频道"

def main():
    if not os.path.exists(INPUT_DIR):
        print(f"❌ 目录 {INPUT_DIR} 不存在")
        return

    print(f"🔄 开始清洗 & 合并 {INPUT_DIR} 中的 multicast_raw_*.m3u 文件...")
    files = [f for f in os.listdir(INPUT_DIR) if f.startswith("multicast_raw_") and f.endswith(".m3u")]
    
    if not files:
        print("未找到任何 multicast_raw_*.m3u 文件")
        return

    print(f"找到 {len(files)} 个文件，开始处理")

    # 用 OrderedDict 去重 + 保留首次出现的顺序
    seen = OrderedDict()  # key: (频道名, URL), value: (info_line, group_simple)

    for filename in sorted(files):
        path = os.path.join(INPUT_DIR, filename)
        print(f"  处理: {filename}")
        
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        i = 0
        while i < len(lines) - 1:
            info = lines[i].strip()
            url = lines[i+1].strip()
            i += 2

            if not info.startswith("#EXTINF") or not url.startswith("http"):
                continue

            channel_name = extract_channel_name(info)
            group_original = re.search(r'group-title="([^"]*)"', info)
            group_simple = simplify_group(group_original.group(1) if group_original else "")

            # 修复 logo：用频道名补全路径
            info = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="https://gcore.jsdelivr.net/gh/taksssss/tv/icon/{channel_name}.png"', info)

            # 更新 group-title 为简化版
            info = re.sub(r'group-title="[^"]*"', f'group-title="{group_simple}"', info)

            key = (channel_name, url)
            if key not in seen:
                seen[key] = (info, group_simple)

    # 生成最终内容
    final_lines = [HEADER]
    for (channel_name, url), (info, _) in seen.items():
        final_lines.append(info)
        final_lines.append(url)

    if len(final_lines) > 1:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(final_lines) + "\n")
        print(f"\n🎉 合并完成！生成 {OUTPUT_FILE}")
        print(f"  唯一频道数: {len(seen)}")
    else:
        print("\n无有效频道，跳过生成")

if __name__ == "__main__":
    main()
