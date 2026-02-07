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
    """通用 JSON 加载"""
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            print(f"⚠️ 读取 {file_path} 异常: {e}")
            return []
    return []

def save_json(file_path, data):
    """通用 JSON 保存"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def run_scan():
    print("\n" + "="*50)
    print("🚀 酒店源基因扫描任务开始 (Actions 持久化版)")
    print("="*50)

    # 1. 加载黑名单 (旧的 old_host 集合)
    blacklist = load_json(BLACKLIST_FILE)
    blacklist_set = set(blacklist)
    print(f"🚫 已加载黑名单记录: {len(blacklist_set)} 条")

    tasks = {} 
    if not os.path.exists(HOTEL_DIR):
        print(f"❌ 错误: 找不到目录 {HOTEL_DIR}")
        return
    
    # 2. 提取基因：遍历 hotel 文件夹下的 m3u
    for file in os.listdir(HOTEL_DIR):
        if file.endswith(".m3u") and not file.startswith("REBORN"):
            file_path = os.path.join(HOTEL_DIR, file)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    # 匹配 http://ip:port/path 格式
                    urls = re.findall(r'http://([\d\.]+:\d+)(/[^\s,]+)', content)
                    for host, path in urls:
                        # 如果该服务器在黑名单中，直接跳过
                        if host in blacklist_set:
                            continue
                        
                        prefix = ".".join(host.split('.')[:3])
                        port = host.split(':')[-1]
                        key = f"{prefix}:{port}"
                        if key not in tasks:
                            tasks[key] = {"old_host": host, "path": path}
            except Exception as e:
                print(f"⚠️ 处理文件 {file} 失败: {e}")

    print(f"📊 待探测有效网段: {len(tasks)} 个")
    if not tasks:
        print("💡 没有新任务，跳过扫描。")
        return

    scan_results = []
    new_dead_hosts = [] # 记录本次全段失效的 old_host
    
    # 3. 逐段探测
    for key, info in tasks.items():
        prefix, port = key.split(':')
        # 构造该 C 段所有 255 个可能的 IP 地址
        scan_list = [f"http://{prefix}.{i}:{port}{info['path']}" for i in range(1, 256)]
        
        valid_found = []
        pbar = tqdm(total=len(scan_list), desc=f"📡 {prefix}.x", bar_format='{l_bar}{bar:20}{r_bar}')
        
        def check_url(url):
            try:
                # 使用 stream=True 避免下载大文件，只检测响应头
                r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)
                if r.status_code == 200:
                    return url
            except:
                pass
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(check_url, u) for u in scan_list]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res:
                    new_host = urlparse(res).netloc
                    valid_found.append(new_host)
                    pbar.write(f"  ✨ [存活] -> {new_host}")
                pbar.update(1)
        pbar.close()
        
        # 判定：如果这一段 1-255 一个活的都没有，把原始 old_host 拉黑
        if not valid_found:
            new_dead_hosts.append(info['old_host'])
            print(f"💀 段 {prefix}.x 确认失效，加入黑名单")
        else:
            for v_host in valid_found:
                scan_results.append({
                    "old_host": info['old_host'], 
                    "new_host": v_host,
                    "path": info['path']
                })

    # 4. 结果持久化
    # 保存存活 IP 映射供 rebuild_m3u.py 使用
    if scan_results:
        save_json(MAP_FILE, scan_results)
        print(f"💾 存活映射已更新: {MAP_FILE}")

    # 更新并保存黑名单
    if new_dead_hosts:
        updated_blacklist = list(set(blacklist + new_dead_hosts))
        save_json(BLACKLIST_FILE, updated_blacklist)
        print(f"🚫 黑名单已同步，当前总数: {len(updated_blacklist)}")

    print("\n" + "="*50)
    print(f"✅ 任务结束。新增存活: {len(scan_results)} | 新拉黑: {len(new_dead_hosts)}")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_scan()
