import os
import re
import json
import requests
import concurrent.futures
from urllib.parse import urlparse
from tqdm import tqdm

HOTEL_DIR = "./hotel"
MAP_FILE = "py/scan_map.json"
TIMEOUT = 3
MAX_WORKERS = 100
HEADERS = {"User-Agent": "Lavf/58.29.100"}

def run_scan():
    tasks = {} 
    if not os.path.exists(HOTEL_DIR): return
    
    # 1. 扫描 hotel 目录提取基因
    print("🧬 正在提取旧 IP 基因...")
    for file in os.listdir(HOTEL_DIR):
        if file.endswith(".m3u") and not file.startswith("REBORN"):
            with open(os.path.join(HOTEL_DIR, file), "r", encoding="utf-8", errors="ignore") as f:
                # 匹配 http://ip:port/path
                urls = re.findall(r'http://([\d\.]+:\d+)(/[^\s,]+)', f.read())
                for host, path in urls:
                    prefix = ".".join(host.split('.')[:3])
                    port = host.split(':')[-1]
                    key = f"{prefix}:{port}"
                    if key not in tasks:
                        tasks[key] = {"old_host": host, "path": path}

    scan_results = []
    # 2. 遍历网段进行爆破
    for key, info in tasks.items():
        prefix, port = key.split(':')
        scan_list = [f"http://{prefix}.{i}:{port}{info['path']}" for i in range(1, 255)]
        
        valid_found = []
        pbar = tqdm(total=len(scan_list), desc=f"📡 扫描 {prefix}.x", leave=False)
        
        def check_url(url):
            try:
                # 只取 Header 快速判断
                r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)
                return url if r.status_code == 200 else None
            except: return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(check_url, u) for u in scan_list]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res:
                    new_host = urlparse(res).netloc
                    valid_found.append(new_host)
                    pbar.write(f"  ✨ [发现存活] {new_host}")
                pbar.update(1)
        pbar.close()
        
        for v_host in valid_found:
            scan_results.append({"old_host": info['old_host'], "new_host": v_host})

    # 3. 存储映射关系
    os.makedirs("py", exist_ok=True)
    with open(MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(scan_results, f, indent=4, ensure_ascii=False)
    print(f"💾 扫描完成，映射关系已保存。")

if __name__ == "__main__":
    run_scan()
