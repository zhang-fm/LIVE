import os
import re

# 配置路径
SOURCE_DIR = "zubo"      # 存放原始 m3u 文件的目录
RTP_TARGET_DIR = "py/rtp" # 生成的 RTP 文本保存目录
LOG_FILE = "py/rtp/mapping_log.txt" # 详细信息记录文件

def extract_and_classify():
    if not os.path.exists(RTP_TARGET_DIR):
        os.makedirs(RTP_TARGET_DIR, exist_ok=True)

    # 用于暂存所有提取到的 RTP 数据：{ "浙江电信": {"CCTV1,rtp://...", ...}, "北京联通": {...} }
    # 使用 set 自动去重
    rtp_data_storage = {}
    log_entries = []
    
    # 遍历源目录下的所有 m3u 文件
    if not os.path.exists(SOURCE_DIR):
        print(f"❌ 找不到源目录: {SOURCE_DIR}")
        return

    for filename in os.listdir(SOURCE_DIR):
        if not filename.endswith(".m3u"):
            continue
            
        file_path = os.path.join(SOURCE_DIR, filename)
        print(f"正在读取: {filename}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"读取失败 {filename}: {e}")
            continue

        # 匹配频道名, 组播信息, RTP地址
        pattern = re.compile(r'#EXTINF:-1.*?group-title="(.*?)",(.*?)\n.*?/rtp/(.*)')
        matches = pattern.findall(content)

        for group_info, channel_name, rtp_addr in matches:
            # 1. 提取运营商/地区名作为文件名
            info_parts = group_info.split()
            isp_name = info_parts[-1] if info_parts else "未知运营商"
            
            # 2. 规范化频道名（去除空格）并组合
            clean_name = channel_name.strip()
            clean_rtp = rtp_addr.strip()
            # 格式: CCTV1,rtp://233.18.204.168:5140
            entry_line = f"{clean_name},rtp://{clean_rtp}"
            
            # 3. 存入内存中的 set 进行去重
            if isp_name not in rtp_data_storage:
                rtp_data_storage[isp_name] = set()
            rtp_data_storage[isp_name].add(entry_line)

            # 4. 记录日志信息
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', filename)
            ip_addr = ip_match.group(1) if ip_match else "未知IP"
            log_entry = f"IP: {ip_addr} | 详细信息: {group_info} | 归类文件: {isp_name}.txt"
            if log_entry not in log_entries:
                log_entries.append(log_entry)

    # --- 写入阶段 ---
    print("💾 正在写入去重后的 RTP 文件...")
    for isp_name, entries in rtp_data_storage.items():
        target_file = os.path.join(RTP_TARGET_DIR, f"{isp_name}.txt")
        
        # 将 set 转换为列表并排序（保证文件内容有序，方便后期对比）
        sorted_entries = sorted(list(entries))
        
        # 使用 'w' 模式写入，覆盖旧的重复数据
        with open(target_file, 'w', encoding='utf-8') as tf:
            for line in sorted_entries:
                tf.write(line + "\n")

    # 写入日志文件
    with open(LOG_FILE, 'w', encoding='utf-8') as lf:
        lf.write("RTP 提取分类记录汇总 (已去重)\n")
        lf.write("="*50 + "\n")
        for entry in sorted(log_entries):
            lf.write(entry + "\n")

    print(f"✅ 处理完成！去重后的文件已保存在 {RTP_TARGET_DIR}")

if __name__ == "__main__":
    extract_and_classify()
