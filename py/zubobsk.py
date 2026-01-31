import requests
import re
import time
import os

# 配置
GITHUB_API_URL = "https://api.github.com/repos/kenye201/LIVE/contents/zubo"
TIMEOUT = 5

def get_file_list():
    print("Fetching file list from GitHub...")
    headers = {}
    if os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {os.getenv('GITHUB_TOKEN')}"
    
    r = requests.get(GITHUB_API_URL, headers=headers)
    r.raise_for_status()
    return [f['download_url'] for f in r.json() if f['name'].endswith('.m3u')]

def test_link_speed(url):
    """在 GitHub Actions 环境下，通常只能测试连接连通性"""
    try:
        start = time.time()
        # 只下载前 128KB 快速判断响应速度
        with requests.get(url, stream=True, timeout=TIMEOUT) as r:
            r.raise_for_status()
            chunk = next(r.iter_content(chunk_size=128*1024))
            duration = time.time() - start
            return round(1 / duration, 2) # 返回响应评分
    except:
        return 0

def process_m3u(file_url):
    name = file_url.split('/')[-1]
    try:
        r = requests.get(file_url, timeout=10)
        content = r.text
        links = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
        
        if not links: return None
        
        # 取前2个链接测试连通性评分
        score = sum(test_link_speed(l) for l in links[:2]) / 2
        return {"name": name, "score": score, "content": content}
    except:
        return None

def main():
    urls = get_file_list()
    results = []

    for url in urls:
        res = process_m3u(url)
        if res:
            results.append(res)
            print(f"Processed: {res['name']} (Score: {res['score']})")

    # 按评分排序
    results.sort(key=lambda x: x['score'], reverse=True)

    with open("zubo.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for res in results:
            clean_content = res['content'].replace("#EXTM3U", "").strip()
            f.write(f"\n# --- Source: {res['name']} ---\n")
            f.write(clean_content + "\n")

if __name__ == "__main__":
    main()
