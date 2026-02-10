import os
import re
import json
import requests
import concurrent.futures
from urllib.parse import urlparse
from tqdm import tqdm

# ================= 配置区 =================
HOTEL_DIR = "./hotel"
MAP_FILE = "py/scan_map.json"
BLACKLIST_FILE = "py/blacklist.json"
TIMEOUT = 3
MAX_WORKERS = 100
HEADERS = {"User-Agent": "Lavf/58.29.100"}
# ==========================================

def load_json(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []
    return []

def save_json(file_path, data):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def check_url(url):
    """单链接探测"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)
        if r.status_code == 200:
            return url
    except:
        pass
    return None

def run_scan():
    print("\n" + "="*50)
    print("🚀 酒店源基因扫描任务 (预检优化版)")
    print("="*50)

    blacklist = set(load_json(BLACKLIST_FILE))
    scan_results = [] # 最终存活映射
    
    # 1. 提取所有原始基因
    raw_genes = [] 
    if not os.path.exists(HOTEL_DIR): return

    for file in os.listdir(HOTEL_DIR):
        if file.endswith(".m3u") and not file.startswith("REBORN"):
            file_path = os.path.join(HOTEL_DIR, file)
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                urls = re.findall(r'http://([\d\.]+:\d+)(/[^\s,]+)', content)
                for host, path in urls:
                    if host not in blacklist:
                        raw_genes.append({"host": host, "path": path})

    # 去重
    unique_genes = {g['host']: g['path'] for g in raw_genes}
    print(f"📋 发现待检测原始 Host: {len(unique_genes)} 个")

    # 2. 第一阶段：预检原始 IP 是否存活
    print(f"🔍 正在进行第一阶段：原始 IP 自检...")
    survived_original_hosts = set()
    to_scan_tasks = {} # 真正需要扫段的

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_host = {executor.submit(check_url, f"http://{h}{p}"): h for h, p in unique_genes.items()}
        for future in concurrent.futures.as_completed(future_to_host):
            host = future_to_host[future]
            if future.result():
                survived_original_hosts.add(host)
                # 自己就是活的，直接存入结果
                scan_results.append({"old_host": host, "new_host": host, "path": unique_genes[host]})
            else:
                # 原始 IP 挂了，准备扫它所在的 C 段
                prefix = ".".join(host.split('.')[:3])
                port = host.split(':')[-1]
                key = f"{prefix}:{port}"
                if key not in to_scan_tasks:
                    to_scan_tasks[key] = {"old_host": host, "path": unique_genes[host]}

    print(f"✅ 自检完成: {len(survived_original_hosts)} 个原始 IP 依然存活")
    print(f"📡 剩余 {len(to_scan_tasks)} 个网段需要扫段复活")

    # 3. 第二阶段：针对失联网段进行 C 段扫描
    new_dead_hosts = []
    for key, info in to_scan_tasks.items():
        prefix, port = key.split(':')
        scan_list = [f"http={prefix}.{i}:{port}{info['path']}" for i in range(1, 256)]
        
        valid_found = []
        pbar = tqdm(total=len(scan_list), desc=f"📡 扫描段 {prefix}.x", bar_format='{l_bar}{bar:20}{r_bar}')
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(check_url, u.replace("http=","http://")) for u in scan_list]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res:
                    new_host = urlparse(res).netloc
                    valid_found.append(new_host)
                    pbar.write(f"  ✨ [复活] -> {new_host}")
                pbar.update(1)
        pbar.close()

        if not valid_found:
            new_dead_hosts.append(info['old_host'])
        else:
            for v_host in valid_found:
                scan_results.append({"old_host": info['old_host'], "new_host": v_host, "path": info['path']})

    # 4. 持久化
    save_json(MAP_FILE, scan_results)
    if new_dead_hosts:
        updated_blacklist = list(set(list(blacklist) + new_dead_hosts))
        save_json(BLACKLIST_FILE, updated_blacklist)

    print(f"\n✨ 扫描结束！总计可用 Host: {len(scan_results)} | 彻底失效拉黑: {len(new_dead_hosts)}")

if __name__ == "__main__":
    run_scan()
