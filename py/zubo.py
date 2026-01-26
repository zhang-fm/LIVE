import asyncio
from playwright.async_api import async_playwright
import re
import os

async def get_real_content():
    async with async_playwright() as p:
        # 1. 启动浏览器
        browser = await p.chromium.launch(headless=True)
        
        # 2. 模拟真实环境参数
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="zh-CN",  # 修复后的参数名
            viewport={'width': 1280, 'height': 800}
        )

        # 3. 隐藏自动化指纹
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
        """)

        page = await context.new_page()
        
        try:
            target_url = "https://iptv.cqshushu.com/index.php"
            print(f"🚀 访问目标: {target_url}")
            
            # 延长超时到 90 秒
            await page.goto(target_url, wait_until="domcontentloaded", timeout=90000)
            
            # --- 模拟真人交互逻辑 ---
            print("🖱️ 正在模拟真人操作以触发 JS 跳转...")
            # 随机移动鼠标
            await page.mouse.move(100, 100)
            await page.mouse.move(400, 300)
            # 模拟轻微滚动
            await page.evaluate("window.scrollTo(0, 200)")
            await asyncio.sleep(1)
            await page.evaluate("window.scrollTo(0, 0)")
            
            # 4. 关键等待：给 JS 盾足够的时间计算并跳转
            # 如果依然只有“请稍候”，我们将等待时间延长到 20 秒
            print("⏳ 等待验证重定向 (20秒)...")
            await page.wait_for_timeout(20000) 

            # 5. 检查是否依然卡在“请稍候”
            content = await page.content()
            if "请稍候" in content and len(content) < 1000:
                print("⚠️ 警告：页面似乎仍卡在验证界面，尝试强制点击页面中心...")
                await page.mouse.click(640, 400)
                await page.wait_for_timeout(10000)
                content = await page.content()

            # 6. 数据处理
            os.makedirs("debug", exist_ok=True)
            print(f"📄 最终源码长度: {len(content)}")
            
            # 提取 IP
            ips = list(dict.fromkeys(re.findall(r"(?:\d{1,3}\.){3}\d{1,3}", content)))
            ips = [ip for ip in ips if not ip.startswith(('127.', '192.168', '10.', '172.', '0.'))]
            
            print(f"✅ 找到有效 IP 数量: {len(ips)}")
            if ips:
                print(f"📡 样本 IP: {ips[:3]}")

            # 保存调试快照
            with open("debug/last_source.html", "w", encoding="utf-8") as f:
                f.write(content)
            await page.screenshot(path="debug/last_view.png")
            
            return ips

        except Exception as e:
            print(f"❌ 运行崩溃: {e}")
            return []
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(get_real_content())
