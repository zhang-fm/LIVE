import re
import os
import concurrent.futures
import requests

# 1. 配置
FILE_PATH = "py/iptv_shushu.html"
# 常用端口字典
PORT_DICT = ["80", "8080", "8000", "81", "8888", "9000"]

def check_url(ip, port):
    """按照 cqshushu 的特定格式拼接并试错"""
    # 构造目标 URL
    test_url = f"https://iptv.cqshushu.com/?s={ip}:{port}&t=multicast&channels=1&download=m3u"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        # 试错下载：由于是下载 m3u，我们检查内容是否包含扩展名特征
        with requests.get(test_url, headers=headers, timeout=5, stream=True) as r:
            if r.status_code == 200:
                # 进一步校验：检查返回的前 100 字节是否包含 #EXTM3U
                content_chunk = r.raw.read(100).decode('utf-8', errors='ignore')
                if "#EXTM3U" in content_chunk:
                    return f"{ip}:{port},{test_url}"
    except:
        pass
    return None

def main():
    if not os.path.exists(FILE_PATH):
        print(f"找不到文件: {FILE_PATH}")
        return

    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # 2. 提取 IP 地址 (匹配常见的 IPv4)
    # 匹配模式：寻找类似 123.123.123.123 的字符串
    ip_list = re.findall(r'(?:\d{1,3}\.){3}\d{1,3}', content)
    # 去重
    unique_ips = list(set(ip_list))
    
    print(f"共提取到 {len(unique_ips)} 个唯一 IP。")
    print(f"使用端口字典: {PORT_DICT}，总计测试次数: {len(unique_ips) * len(PORT_DICT)}")

    # 3. 构造任务池
    tasks = []
    for ip in unique_ips:
        for port in PORT_DICT:
            tasks.append((ip, port))

    # 4. 并发测试
    print("开始并发试错...")
    valid_results = []
    # 调高并发数，加快试错速度
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        future_to_task = {executor.submit(check_url, ip, port): (ip, port) for ip, port in tasks}
        
        for future in concurrent.futures.as_completed(future_to_task):
            result = future.result()
            if result:
                valid_results.append(result)
                print(f"[成功] {result.split(',')[0]} -> 可下载")

    # 5. 输出最终结果
    print("\n" + "="*30)
    print(f"探测结束，共发现 {len(valid_results)} 个有效源：")
    for item in valid_results:
        print(item)

if __name__ == "__main__":
    main()
