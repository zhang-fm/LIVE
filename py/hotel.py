import requests
import re
from urllib.parse import urljoin

BASE_URL = "https://iptv.cqshushu.com/"
LIST_URL = "https://iptv.cqshushu.com/?t=hotel"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def get_hotel_ip_list():
    """
    抓取 Hotel IPTV 第 1 页的 IP 列表
    """
    resp = requests.get(LIST_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    html = resp.text

    # 匹配 IP 或 IP:端口（页面中是作为 ?s=xxx 出现的）
    ips = set(re.findall(
        r'\?s=([0-9\.]+(?::\d+)?)&t=hotel',
        html
    ))

    print(f"发现 {len(ips)} 个 Hotel IPTV IP")
    return sorted(ips)


def get_m3u_download_link(ip):
    """
    进入单个 IP 页面，提取 M3U 下载链接
    """
    detail_url = f"{BASE_URL}?s={ip}&t=hotel"
    resp = requests.get(detail_url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    html = resp.text

    # 精确匹配 m3u 下载
    match = re.search(
        r"href='(\?s=[^']+&t=hotel&channels=1&download=m3u)'",
        html
    )

    if not match:
        print(f"[跳过] {ip} 未找到 M3U 下载")
        return None

    relative_link = match.group(1)
    full_link = urljoin(BASE_URL, relative_link)
    return full_link


def main():
    ips = get_hotel_ip_list()

    results = []
    for ip in ips:
        print(f"处理 {ip}")
        m3u = get_m3u_download_link(ip)
        if m3u:
            results.append(m3u)
            print(f"  ✔ {m3u}")

    # 保存结果
    with open("hotel_m3u_links.txt", "w", encoding="utf-8") as f:
        for url in results:
            f.write(url + "\n")

    print(f"\n完成，共获取 {len(results)} 条 M3U 链接")


if __name__ == "__main__":
    main()
