import os
import re
import random
import requests
import concurrent.futures
from urllib.parse import urlparse

# ===============================
# 配置区
# ===============================
HOTEL_DIR = "./hotel"       # 酒店源目录
TIMEOUT = 3                 # 探测超时
MAX_WORKERS = 100           # 并发数
HEADERS = {"User-Agent": "Lavf/58.29.100"}

# ===============================
# 核心扫描逻辑
# ===============================

def get_smart_tasks():
    """
    智能解析：合并前三位相同的IP，保留不同网段的特征
    """
    tasks = {} # Key: "prefix:port", Value: suffix_path
    
    if not os.path.exists(HOTEL_DIR):
        print("❌ 找不到 hotel 文件夹")
        return []

    print("🧹 正在扫描现有库并合并同类项...")
    
    for file in os.listdir(HOTEL_DIR):
        if not file.endswith(".m3u"): continue
        
        with open(os.path.join(HOTEL_DIR, file), "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            # 找到所有 http 链接
            urls = [l.strip() for l in lines if l.startswith("http")]
            
            for url in urls:
                parsed = urlparse(url)
                netloc = parsed.netloc # 例如 171.43.64.63:85
                host_parts = netloc.split(':')
                ip = host_parts[0]
                port = host_parts[1] if len(host_parts) > 1 else "80"
                
                ip_parts = ip.split('.')
                if len(ip_parts) == 4:
                    # 提取前三位作为合并标准
                    prefix = ".".join(ip_parts[:3]) 
                    key = f"{prefix}:{port}"
                    
                    # 如果该网段还没存入，或者存入的是空的，则保存路径
                    if key not in tasks:
                        tasks[key] = parsed.path + "?" + parsed.query
    
    print(f"🧬 归类完成，共识别出 {len(tasks)} 个唯一的 C 段网段")
    return tasks

def check_ip(url):
    """单个 URL 连通性测试"""
    try:
        # 酒店源探测，GET 并只取少量数据即可
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)
        if r.status_code == 200:
            return url
    except:
        pass
    return None

def run():
    tasks = get_smart_tasks()
    if not tasks: return

    all_discovered_nodes = []

    for key, suffix in tasks.items():
        prefix, port = key.split(':')
        print(f"📡 正在探测 C 段: {prefix}.1~254 (端口: {port})")
        
        # 构造 1-254 的扫描列表
        scan_list = [f"http://{prefix}.{i}:{port}{suffix}" for i in range(1, 255)]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 过滤掉 None 结果
            results = list(filter(None, executor.map(check_ip, scan_list)))
        
        if results:
            print(f"   ✅ 发现 {len(results)} 个存活节点！")
            all_discovered_nodes.extend(results)
        else:
            print(f"   ❌ 该段暂无存活。")

    # --- 最终汇总 ---
    if all_discovered_nodes:
        # 提取这些有效 URL 的 IP 和端口，方便你后续批量替换
        valid_hosts = sorted(list(set([urlparse(u).netloc for u in all_discovered_nodes])))
        
        with open("active_hotel_hosts.txt", "w", encoding="utf-8") as f:
            for host in valid_hosts:
                f.write(host + "\n")
        
        print(f"\n✨ 扫描大功告成！")
        print(f"📝 所有存活的酒店 IP 端口已存入: active_hotel_hosts.txt")
        print(f"🚀 你现在可以用这些新 IP 替换旧 m3u 里的地址了。")

if __name__ == "__main__":
    run()
