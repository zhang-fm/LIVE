import os
import re
import random
import requests
import concurrent.futures
from urllib.parse import urlparse
from tqdm import tqdm  # 引入进度条库

# ===============================
# 配置区
# ===============================
HOTEL_DIR = "./hotel"
TIMEOUT = 3
MAX_WORKERS = 100
HEADERS = {"User-Agent": "Lavf/58.29.100"}

def get_smart_tasks():
    """解析并合并网段"""
    tasks = {}
    if not os.path.exists(HOTEL_DIR):
        return {}

    print("Step 1: 🔍 正在分析现有库文件...")
    for file in os.listdir(HOTEL_DIR):
        if not file.endswith(".m3u"): continue
        with open(os.path.join(HOTEL_DIR, file), "r", encoding="utf-8", errors="ignore") as f:
            urls = re.findall(r'http://[^\s,]+', f.read())
            for url in urls:
                parsed = urlparse(url)
                host_parts = parsed.netloc.split(':')
                ip = host_parts[0]
                port = host_parts[1] if len(host_parts) > 1 else "80"
                ip_parts = ip.split('.')
                if len(ip_parts) == 4:
                    prefix = ".".join(ip_parts[:3]) 
                    key = f"{prefix}:{port}"
                    if key not in tasks:
                        tasks[key] = parsed.path + "?" + parsed.query
    return tasks

def check_ip(url):
    """探测单个 IP，返回结果供进度条实时显示"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)
        if r.status_code == 200:
            return url
    except:
        pass
    return None

def run():
    tasks = get_smart_tasks()
    if not tasks:
        print("❌ 未发现可扫描的特征。")
        return

    print(f"🧬 识别到 {len(tasks)} 个唯一 C 段。即将开始扫描...")
    
    all_discovered = []
    
    # 逐个网段扫描，展示详细过程
    for key, suffix in tasks.items():
        prefix, port = key.split(':')
        scan_list = [f"http://{prefix}.{i}:{port}{suffix}" for i in range(1, 255)]
        
        # 使用 tqdm 展示当前网段的扫描进度
        # desc 设置左侧描述，leave=False 扫描完一个段后清除该进度条，保持界面整洁
        pbar = tqdm(total=len(scan_list), desc=f"📡 扫描中 {prefix}.x", unit="ip", leave=True)
        
        valid_in_segment = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(check_ip, url) for url in scan_list]
            
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res:
                    valid_in_segment.append(res)
                    # 当发现有效 IP 时，在进度条上方打印一条成功记录
                    pbar.write(f"  ✨ [发现存活] {res}")
                pbar.update(1) # 每完成一个任务，进度条前进 1
        
        pbar.close() # 结束当前段进度条
        if valid_in_segment:
            all_discovered.extend(valid_in_segment)
            print(f"✅ 网段 {prefix}.x 扫描完成，新增 {len(valid_in_segment)} 个节点")

    # 保存最终结果
    if all_discovered:
        hosts = sorted(list(set([urlparse(u).netloc for u in all_discovered])))
        with open("active_hotel_hosts.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(hosts))
        print(f"\n🎉 扫描结束！共发现 {len(hosts)} 个存活酒店主机。")

if __name__ == "__main__":
    run()
