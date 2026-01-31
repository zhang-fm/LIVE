import asyncio
import random
import re
from playwright.async_api import async_playwright

async def apply_stealth(page):
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        window.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh'] });
    """)

async def main():
    async with async_playwright() as p:
        # 增加忽略 HTTPS 错误，有时拦截页会有证书问题
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )
        
        page = await context.new_page()
        await apply_stealth(page)

        url = "https://iptv.cqshushu.com/"
        print(f"🚀 访问目标: {url}")
        
        try:
            # 尝试访问
            response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            print(f"📡 HTTP 状态码: {response.status if response else '无响应'}")
            
            await asyncio.sleep(8) # 等待潜在的 JS 挑战跳转
            
            title = await page.title()
            print(f"📑 网页标题: {title}")

            # 侦察
            links = await page.query_selector_all("a")
            print(f"🔎 侦察报告：页面当前共有 {len(links)} 个链接。")
            
            # 修复 Locator 逻辑
            # 使用 locator 的 count() 检查是否存在
            ip_locator = page.get_by_role("link").filter(has_text=re.compile(r'\d+\.\d+\.\d+\.\d+'))
            
            if await ip_locator.count() > 0:
                print("✅ 找到 IP 格式链接，尝试点击...")
                target = ip_locator.first
                await target.scroll_into_view_if_needed()
                
                async with page.expect_navigation(wait_until="networkidle", timeout=60000):
                    await target.click()
                
                print(f"🎉 进入详情页: {page.url}")
                await page.screenshot(path="detail_success.png")
            else:
                # 如果没找到，尝试按 class 模糊找
                fuzzy_ip = await page.query_selector("a[class*='ip']")
                if fuzzy_ip:
                    print("✅ 找到模糊匹配链接，点击...")
                    await fuzzy_ip.click()
                else:
                    print("❌ 依然未发现目标。请下载 final_state.png 查看拦截详情。")
                    await page.screenshot(path="final_state.png")

        except Exception as e:
            print(f"❌ 运行异常: {e}")
            await page.screenshot(path="error_state.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
