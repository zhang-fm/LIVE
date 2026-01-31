import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor
import os

# 配置
GITHUB_API_URL = "https://api.github.com/repos/kenye201/LIVE/contents/zubo"
TIMEOUT = 3  # 检测超时
TEST_DURATION = 3  # 每个链接测速时长（秒）

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    # 如果频繁运行，建议填入你的 GitHub Token 避免限速
    # "Authorization": "token YOUR_GITHUB_TOKEN"
}

def get_file_list():
    print("正在从 GitHub 获取文件列表...")
    r = requests.get(GITHUB_API_URL, headers=headers)
    r.raise_for_status()
    return [f['download_url'] for f in r.json() if f['name'].endswith('.m3u')]

def test_speed(url):
    """测试下载速度 (Mbps)"""
    try:
        start_time = time.time()
        size = 0
        # 使用 stream=True 边下载边测速
        with requests.get(url, stream=True, timeout=TIMEOUT) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=1024*32):
                size += len(chunk)
                if time.time() - start_time > TEST_DURATION:
                    break
        
        duration = time.time() - start_time
        mbps = (size * 8) / (duration * 1024 * 1024)
        return round(mbps, 2)
    except:
        return 0

def process_m3u(file_url):
    print(f"处理文件: {file_url.split('/')[-1]}")
    try:
        r = requests.get(file_url, timeout=10)
        content = r.text
        # 提取所有 http 链接
        links = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
        
        if not links:
            return None
        
        # 提取前 2 个链接进行测速
        test_links = links[:2]
        speeds = []
        for l in test_links:
            s = test_speed(l)
            if s > 0: speeds.append(s)
        
        avg_speed = sum(speeds) / len(speeds) if speeds else 0
        return {
            "name": file_url.split('/')[-1],
            "speed": avg_speed,
            "content": content
        }
    except Exception as e:
        print(f"解析出错: {file_url} - {e}")
        return None

def main():
    urls = get_file_list()
    results = []

    print(f"共发现 {len(urls)} 个文件，开始并发测速...")
    # 线程数不宜过高，否则可能导致本地网络拥塞影响测速结果
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_m3u, url) for url in urls]
        for f in futures:
            res = f.result()
            if res and res['speed'] > 0:
                results.append(res)
                print(f"✅ {res['name']} - 平均速度: {res['speed']} Mbps")

    # 按速度从高到低排序
    results.sort(key=lambda x: x['speed'], reverse=True)

    if not results:
        print("❌ 未发现任何可访问的有效组播链接。")
        return

    # 合成新的 m3u
    print(f"正在生成汇总文件 zubo.m3u (共选取 {len(results)} 个 IP 段)...")
    with open("zubo.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for res in results:
            # 过滤掉原始 content 中的 #EXTM3U 头部，避免重复
            clean_content = res['content'].replace("#EXTM3U", "").strip()
            f.write(f"\n# --- 来源: {res['name']} (测速: {res['speed']} Mbps) ---\n")
            f.write(clean_content + "\n")

    print("🎉 任务完成！结果已保存至 zubo.m3u")

if __name__ == "__main__":
    main()
