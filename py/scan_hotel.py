import os, re, json, requests, concurrent.futures
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
    
    # 1. 提取基因 (过滤掉旧的 REBORN 文件，只从原始库提取)
    print("🧬 正在分析原始酒店基因库...")
    for file in os.listdir(HOTEL_DIR):
        if file.endswith(".m3u") and not file.startswith("REBORN"):
            with open(os.path.join(HOTEL_DIR, file), "r", encoding="utf-8", errors="ignore") as f:
                urls = re.findall(r'http://([\d\.]+:\d+)(/[^\s,]+)', f.read())
                for host, path in urls:
                    prefix = ".".join(host.split('.')[:3])
                    port = host.split(':')[-1]
                    key = f"{prefix}:{port}"
                    if key not in tasks:
                        tasks[key] = {"old_host": host, "path": path}

    scan_results = []
    # 2. 并发扫描
    print(f"📡 开始实时探测 {len(tasks)} 个目标网段...")
    for key, info in tasks.items():
        prefix, port = key.split(':')
        scan_list = [f"http://{prefix}.{i}:{port}{info['path']}" for i in range(1, 255)]
        
        valid_found = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 使用列表推导式配合 requests 探测
            futures = {executor.submit(lambda u: requests.get(u, headers=HEADERS, timeout=TIMEOUT, stream=True).status_code == 200, url): url for url in scan_list}
            for future in concurrent.futures.as_completed(futures):
                try:
                    if future.result():
                        res_url = futures[future]
                        valid_found.append(urlparse(res_url).netloc)
                except: pass
        
        for v_host in valid_found:
            print(f"  ✨ [核心存活] {v_host}")
            scan_results.append({"old_host": info['old_host'], "new_host": v_host})

    # 3. 保存映射
    os.makedirs("py", exist_ok=True)
    with open(MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(scan_results, f, indent=4, ensure_ascii=False)
    print(f"💾 映射表更新完成，共计 {len(scan_results)} 个最新活跃节点。")

if __name__ == "__main__":
    run_scan()
