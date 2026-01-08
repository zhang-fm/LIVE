import asyncio
import base64
import os
import re
from playwright.async_api import async_playwright

BASE_URL = "https://iptv.cqshushu.com/?t=hotel"
OUT_FILE = "test/hotel_m3u_links.txt"

async def main():
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)

    async with async_playwright() as p:
        # 启动 Chromium 浏览器（无头）
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/117.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
        )
        page = await context.new_page()

        print("="*80)
        print(f"访问首页: {BASE_URL}", flush=True)
        try:
            await page.goto(BASE_URL, timeout=60000)
            await page.wait_for_timeout(3000)  # 等 3 秒，等待 JS 渲染
            print("[成功] 首页加载完成", flush=True)
        except Exception as e:
            print(f"[异常] 首页访问失败: {e}", flush=True)
            await browser.close()
            return

        # 获取所有 IP
        ip_elements = await page.query_selector_all("a.ip-link")
        ips = []
        for el in ip_elements:
            onclick_attr = await el.get_attribute("onclick")
            if onclick_attr:
                m = re.search(r"gotoIP\('([^']+)'", onclick_attr)
                if m:
                    try:
                        ip = base64.b64decode(m.group(1)).decode()
                        ips.append(ip)
                    except Exception as e:
                        print(f"[异常] base64 decode 失败: {e}", flush=True)

        print(f"✔ 发现 IP 数量: {len(ips)}", flush=True)
        print(f"IP 列表: {ips}", flush=True)

        all_links = []

        for ip in ips:
            print(f"\n处理 IP: {ip}", flush=True)
            try:
                # 模拟点击 IP 进入详情页
                await page.evaluate(f"""
                    () => {{
                        const ipEl = Array.from(document.querySelectorAll('a.ip-link'))
                                      .find(el => el.textContent.includes('{ip}'));
                        if(ipEl) ipEl.click();
                    }}
                """)
                # 等待下载 M3U 链接出现
                await page.wait_for_selector("div.download-section a.download-btn.m3u", timeout=15000)
                m3u_link_el = await page.query_selector("div.download-section a.download-btn.m3u")
                if m3u_link_el:
                    href = await m3u_link_el.get_attribute("href")
                    full_link = f"http://iptv.cqshushu.com/{href.lstrip('?')}"
                    all_links.append(full_link)
                    print(f"  └─ M3U 链接: {full_link}", flush=True)
                else:
                    print(f"  └─ 未找到 M3U 下载链接", flush=True)
            except Exception as e:
                print(f"  └─ [异常] {e}", flush=True)

        await browser.close()

    # 保存结果
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for link in sorted(set(all_links)):
            f.write(link + "\n")

    print("="*80)
    print(f"完成，共获取 {len(all_links)} 条 M3U", flush=True)
    print(f"保存至 {OUT_FILE}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
