import asyncio
from playwright.async_api import async_playwright
import re
import os
import time

async def get_real_content():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # 模拟一个非常真实的 Mac Chrome 环境
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="zh-CN"
        )

        page = await context.new_page()
        
        # --- 核心黑科技：手动注入验证 Cookie ---
        # 这里的 '6721feb1cc146bf5' 是从你之前发的源码里提取的固定前缀
        # 网站校验逻辑：前缀 + '_' + 时间戳
        fake_cookie_value = f"6721feb1cc146bf5_{int(time.time() * 1000)}"
        
        await context.add_cookies([{
            'name': 'list_js_verified',
            'value': fake_cookie_value,
            'domain': 'iptv.cqshushu.com',
            'path': '/'
        }])
        print(f"🔑 已注入伪造 Cookie: {fake_cookie_value}")

        try:
            # 注入后直接访问带参数的地址，强制跳过验证页面
            target_url = "https://iptv.cqshushu.com/index.php?_js=1"
            print(f"🚀 尝试直达目标: {target_url}")
            
            await page.goto(target_url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(5000) # 给页面渲染留 5 秒

            content = await page.content()
            print(f"📄 最终源码长度: {len(content)}")

            # 提取 IP
            ips = list(dict.fromkeys(re.findall(r"(?:\d{1,3}\.){3}\d{1,3}", content)))
            ips = [ip for ip in ips if not ip.startswith(('127.', '192.', '10.', '172.', '0.'))]
            
            # 调试保存
            os.makedirs("debug", exist_ok=True)
            with open("debug/force_source.html", "w", encoding="utf-8") as f:
                f.write(content)
            await page.screenshot(path="debug/force_view.png")

            if len(ips) > 0:
                print(f"✅ 成功绕过！抓取到 {len(ips)} 个 IP")
                # 这里可以保存你的 m3u 逻辑...
            else:
                print("❌ 依然没有抓到 IP，可能页面内容被加密或混淆了")

            return ips

        except Exception as e:
            print(f"❌ 运行失败: {e}")
            return []
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(get_real_content())
