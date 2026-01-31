import asyncio
import random
from playwright.async_api import async_playwright

async def apply_stealth(page):
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        window.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh'] });
    """)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # 模拟手机端或更高分辨率，有时能避开 PC 端的强力检测
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        await apply_stealth(page)

        url = "https://iptv.cqshushu.com/"
        print(f"🚀 访问目标: {url}")
        
        try:
            # 1. 延长加载时间，等待网络彻底空闲
            await page.goto(url, wait_until="networkidle", timeout=90000)
            
            # 2. 强制等待 10 秒，给 Ajax 结果留出渲染时间
            print("⏳ 等待页面动态渲染...")
            await asyncio.sleep(10)
            
            # 3. 侦察：打印当前页面所有 a 标签的数量和部分文本
            links = await page.query_selector_all("a")
            print(f"🔎 侦察报告：页面当前共有 {len(links)} 个链接。")
            
            # 4. 尝试更宽泛的选择器 (只要包含 ip 关键字或者符合链接特征)
            # 这里的 selector 尝试匹配 class 包含 ip 的所有 a 标签
            ip_link = await page.query_selector("a[class*='ip'], a[href*='p=']")
            
            if not ip_link:
                # 最后的挣扎：搜索包含数字点格式的文字链接 (类似 IP 格式)
                ip_link = await page.get_by_role("link").filter(has_text=re.compile(r'\d+\.\d+\.\d+\.\d+')).first
            
            if ip_link:
                print("✅ 找到疑似 IP 链接，尝试点击...")
                await ip_link.scroll_into_view_if_needed()
                
                async with page.expect_navigation(wait_until="networkidle", timeout=60000):
                    await ip_link.click()
                
                print(f"🎉 进入详情页: {page.url}")
                await page.screenshot(path="detail_success.png")
            else:
                print("❌ 依然未发现目标元素。")
                # 记录“犯罪现场”，这是最重要的调试依据
                await page.screenshot(path="final_state.png")
                # 打印前 500 个字符源码，看是否有报错信息
                content = await page.content()
                print(f"📄 页面源码片段: {content[:500]}")

        except Exception as e:
            print(f"❌ 运行异常: {e}")
            await page.screenshot(path="error_state.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    import re # 别忘了导入正则
    asyncio.run(main())
