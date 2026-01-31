import asyncio
import random
from playwright.async_api import async_playwright

async def apply_stealth(page):
    """
    手动注入 Stealth 脚本，绕过 WebDriver 检测。
    这替代了报错连连的 playwright_stealth 库。
    """
    await page.add_init_script("""
        // 抹除 navigator.webdriver 标记
        Object.defineProperty(navigator, 'webdriver', { get: () => fales });
        // 伪造 Chrome 插件信息
        window.chrome = { runtime: {} };
        // 伪造语言和权限
        Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    """)

async def simulate_human_behavior(page):
    print("正在执行人类行为模拟...")
    for _ in range(random.randint(2, 4)):
        await page.mouse.wheel(0, random.randint(200, 600))
        await asyncio.sleep(random.uniform(1, 2))

async def main():
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1344, 'height': 840}
        )
        
        page = await context.new_page()
        
        # 应用手动伪装
        await apply_stealth(page)

        url = "https://iptv.cqshushu.com/"
        print(f"🚀 访问目标: {url}")
        
        try:
            # 增加超时容忍度
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)
            await simulate_human_behavior(page)
            
            # 定位并点击第一个有效 IP 链接
            ip_link = await page.query_selector("a.ip-link")
            
            if ip_link:
                print("✅ 找到链接，模拟点击...")
                await ip_link.scroll_into_view_if_needed()
                box = await ip_link.bounding_box()
                
                # 在点击的同时等待跳转
                async with page.expect_navigation(wait_until="networkidle", timeout=60000):
                    await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                
                print(f"🎉 详情页跳转成功: {page.url}")
                await page.screenshot(path="detail_page.png")
                
                html = await page.content()
                with open("detail.txt", "w", encoding="utf-8") as f:
                    f.write(html)
            else:
                print("❌ 页面未发现 .ip-link 元素")
                await page.screenshot(path="no_element.png")

        except Exception as e:
            print(f"❌ 运行异常: {e}")
            await page.screenshot(path="error_state.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
