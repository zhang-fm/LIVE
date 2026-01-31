import asyncio
import re
from playwright.async_api import async_playwright

async def apply_stealth(page):
    """手动注入基础伪装"""
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        window.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh'] });
    """)

async def main():
    async with async_playwright() as p:
        # 使用无头模式模拟 GitHub Actions 环境
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1344, 'height': 840}
        )
        
        page = await context.new_page()
        await apply_stealth(page)

        # 【测试目标】直接使用你抓取到的完整长链接
        # 注意：这里的 token 可能有时效性，如果报错 403，可能需要换一个新的 token 链接
        test_url = "https://iptv.cqshushu.com/?p=119.128.153.93&t=multicast&_t=1769870857064&paer_token=1769870857%7C%7B%22ua%22%3A%22Mozilla%2F5.0%20(Windows%20NT%2010.0%3B%20Win64%3B%20x64)%20AppleWebKit%2F537.36%20(KHTML%2C%20like%20Gecko)%20Chrome%2F144.0.0.0%20Safari%2F537.36%22%2C%22lang%22%3A%22zh-CN%22%2C%22timezone%22%3A%22Asia%2FShanghai%22%2C%22screen%22%3A%221344x840%22%2C%22colorDepth%22%3A24%2C%22platform%22%3A%22Win32%22%2C%22cookieEnabled%22%3Atrue%2C%22doNotTrack%22%3A%22unknown%22%2C%22loadTime%22%3A1516%7D%7C%7B%22clickTime%22%3A1769870857065%2C%22mouseMoves%22%3A0%2C%22scrolls%22%3A0%7D%7C7ezgz5i0bde%7C536307f1a0306fca84e6ce1f36c35fd46d86544634a7825702d39fdd84c4433b"

        print(f"🧪 开始实验：直接挑战详情页 URL...")
        
        try:
            # 访问页面
            response = await page.goto(test_url, wait_until="domcontentloaded", timeout=60000)
            print(f"📡 响应状态码: {response.status if response else 'N/A'}")
            
            # 等待一段时间，看是否会自动从“验证中”跳转
            print("⏳ 等待 15 秒观察是否触发 5 秒盾...")
            await asyncio.sleep(15)
            
            title = await page.title()
            print(f"📑 最终页面标题: {title}")
            
            # 核心测试：寻找那个按钮
            # 使用多种方式探测按钮是否存在
            btn_text = "查看频道列表"
            button = page.get_by_role("button", name=re.compile(btn_text))
            
            if "验证中" in title or "Just a moment" in title:
                print("❌ 结果：依然触发了 Cloudflare 验证盾。")
            elif await button.count() > 0:
                print(f"✅ 成功！绕过验证，发现了‘{btn_text}’按钮。")
                await button.first.scroll_into_view_if_needed()
                await page.screenshot(path="experiment_success.png")
            else:
                print("⚠️ 标题正常但未发现按钮，可能 Token 已过期或页面布局不同。")
                await page.screenshot(path="experiment_unknown.png")
                
            # 打印部分源码辅助判断
            content = await page.content()
            print(f"📄 源码片段: {content[:300]}...")

        except Exception as e:
            print(f"❌ 实验异常: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
