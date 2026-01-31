import asyncio
import random
import re
from playwright.async_api import async_playwright
# 直接导入模块，避免导入特定的函数名
import playwright_stealth

async def simulate_human_behavior(page):
    """模拟人类浏览：滚动和鼠标移动"""
    print("正在模拟人类浏览行为...")
    for _ in range(random.randint(2, 4)):
        scroll_y = random.randint(300, 600)
        await page.mouse.wheel(0, scroll_y)
        await asyncio.sleep(random.uniform(0.8, 2.0))
    await page.mouse.move(random.randint(100, 600), random.randint(100, 600))

async def main():
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1344, 'height': 840}
        )
        
        page = await context.new_page()
        
        # --- 核心修复部分 ---
        try:
            # 尝试最常见的异步调用
            await playwright_stealth.stealth_async(page)
        except AttributeError:
            try:
                # 尝试通用的同步/异步包装调用
                await playwright_stealth.stealth_page(page)
            except Exception:
                # 如果都失败，直接调用模块本身（部分版本支持）
                from playwright_stealth import stealth_page
                await stealth_page(page)
        # ------------------

        url = "https://iptv.cqshushu.com/"
        print(f"🚀 正在打开主页: {url}")
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(3)
            await simulate_human_behavior(page)
            
            # 定位并点击第一个 IP 链接
            ip_link = await page.query_selector("a.ip-link")
            if ip_link:
                print(f"✅ 找到 IP 链接，执行模拟点击进入详情页...")
                
                # 滚动并点击
                await ip_link.scroll_into_view_if_needed()
                box = await ip_link.bounding_box()
                
                async with page.expect_navigation(wait_until="networkidle", timeout=60000):
                    await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                
                print(f"🎉 成功到达详情页: {page.url}")
                await page.screenshot(path="detail_page.png")
                
                # 抓取源码
                html = await page.content()
                with open("detail.html", "w", encoding="utf-8") as f:
                    f.write(html)
            else:
                print("❌ 未能在主页找到 ip-link")
                await page.screenshot(path="home_error.png")

        except Exception as e:
            print(f"❌ 运行中发生错误: {e}")
            await page.screenshot(path="crash_error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
