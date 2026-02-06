import os, re, json, requests, concurrent.futures
from urllib.parse import urlparse
from tqdm import tqdm

HOTEL_DIR = "./hotel"
MAP_FILE = "py/scan_map.json"
TIMEOUT = 3
MAX_WORKERS = 100
HEADERS = {"User-Agent": "Lavf/58.29.100"}

def run_scan():
    print("\n" + "="*50)
    print("🚀 酒店源基因扫描任务开始")
    print("="*50)

    tasks = {} 
    if not os.path.exists(HOTEL_DIR):
        print(f"❌ 错误: 找不到目录 {HOTEL_DIR}")
        return
    
    # 提取基因
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

    print(f"📊 已提取特征网段: {len(tasks)} 个")
    
    scan_results = []
    
    for key, info in tasks.items():
        prefix, port = key.split(':')
        scan_list = [f"http://{prefix}.{i}:{port}{info['path']}" for i in range(1, 255)]
        
        valid_found = []
        # desc 让进度条显示当前正在扫哪个段
        pbar = tqdm(total=len(scan_list), desc=f"📡 探测 {prefix}.x", bar_format='{l_bar}{bar:20}{r_bar}')
        
        def check_url(url):
            try:
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
                    # pbar.write 可以保证打印信息不破坏进度条结构
                    pbar.write(f"  ✨ [前台发现存活] -> {new_host}")
                pbar.update(1)
        pbar.close()
        
        for v_host in valid_found:
            scan_results.append({"old_host": info['old_host'], "new_host": v_host})

    os.makedirs("py", exist_ok=True)
    with open(MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(scan_results, f, indent=4, ensure_ascii=False)
    
    print("\n" + "="*50)
    print(f"✅ 扫描阶段结束，共捕获 {len(scan_results)} 个活跃 IP")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_scan()
