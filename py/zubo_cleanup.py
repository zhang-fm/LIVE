import os
import re
import requests
import concurrent.futures
import time

# ===============================
# 配置区
# ===============================
ZUBO_DIR = "zubo"
SAMPLE_COUNT = 3               # 抽测 3 个频道，只要有 1 个通就行
CHECK_TIMEOUT = 15             # 连接超时加长到 15s
STREAM_READ_TIMEOUT = 10       # 读取流数据等待加长
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def check_zubo_stream(url):
    """
    深度检测：连通性 + 缓冲推流检测
    """
    try:
        # 1. 建立流连接
        response = requests.get(url, headers=HEADERS, timeout=CHECK_TIMEOUT, stream=True)
        
        if response.status_code == 200:
            # 2. 稍微等一下，给服务器建立缓冲区的时间
            time.sleep(2) 
            
            # 3. 尝试读取数据块
            # 使用迭代器读取，如果 10s 内能读到任何内容即为有效
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    return True 
                break 
        return False
    except:
        return False
    finally:
        try: response.close()
        except: pass

def is_zubo_file_alive(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        links = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
        if not links: return False
        
        # 抽取样本
        test_links = links[:SAMPLE_COUNT]
        
        # 这里不使用并发，而是顺序检测，给每个链接充分的测试环境
        for link in test_links:
            if check_zubo_stream(link):
                return True
            time.sleep(1) # 链接探测间隔
            
        return False
    except Exception as e:
        print(f" ⚠️ 错误: {e}", end="")
        return False

def main():
    if not os.path.exists(ZUBO_DIR): return

    print(f"🔍 开始深度清理失效组播源...")
    files = [f for f in os.listdir(ZUBO_DIR) if f.endswith(".m3u")]
    
    removed_count = 0
    for filename in files:
        file_path = os.path.join(ZUBO_DIR, filename)
        print(f"📡 正在检测: {filename} ... ", end="", flush=True)
        
        # 执行深度检测
        if not is_zubo_file_alive(file_path):
            print("❌ 确认为死链 (已删除)")
            os.remove(file_path)
            removed_count += 1
        else:
            print("✅ 正常存活")
        
        # 文件之间稍微停顿，避免请求过快被服务器封锁
        time.sleep(2)

    print(f"\n✨ 清理完成！共删除 {removed_count} 个失效文件。")

if __name__ == "__main__":
    main()
