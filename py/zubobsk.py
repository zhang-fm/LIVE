import asyncio
import os
import re
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1344, 'height': 840}
        )
        page = await context.new_page()

        # 1. 定位本地 HTML 文件
        # GitHub Actions 的工作目录通常是 /home/runner/work/LIVE/LIVE/
        html_path = os.path.abspath("data/shushu_home.html")
        
        if not os.path.exists(html_path):
            print(f"❌ 找不到文件: {html_path}")
            # 打印当前目录结构辅助调试
            print("当前目录列表:")
            for root, dirs, files in os.walk("."):
                for name in files:
                    if "shushu_home" in name:
                        print(f"找到可能的文件: {os.path.join(root, name)}")
            return

        print(f"📂 正在加载本地首页: {html_path}")
        await page.goto(f"file://{html_path}")
        await asyncio.sleep(2)

        # 2. 定位 IP 链接并点击
        # 目标链接通常是 <a class="ip-link" ...>
        ip_link = await page.query_selector("a.ip-link")
        
        if ip_link:
            print("✅ 成功在本地 HTML 中找到 IP 链接。")
            link_text = await ip_link.inner_text()
            print(f"🔗 准备点击 IP: {link_text.strip()}")

            try:
                # 监听点击后的跳转
                print("🚀 正在触发点击跳转到目标服务器...")
                async with page.expect_navigation(timeout=60000):
                    await ip_link.click()
                
                # 给详情页留出通过验证的时间
                print(f"📡 已跳转，当前 URL: {page.url}")
                print("⏳ 等待 15 秒观察 Cloudflare 验证状态...")
                await asyncio.sleep(15)
                
                title = await page.title()
                print(f"📑 最终页面标题: {title}")
                
                # 检查是否看到了“查看频道列表”按钮
                btn = page.get_by_role("button", name=re.compile("查看频道列表"))
                if await btn.count() > 0:
                    print("🎉 奇迹发生了！绕过验证看到了按钮。")
                    await page.screenshot(path="jump_success.png")
                else:
                    print("❌ 依然显示验证页或 403。")
                    await page.screenshot(path="jump_fail.png")

            except Exception as e:
                print(f"❌ 跳转过程中发生错误: {e}")
                await page.screenshot(path="jump_error.png")
        else:
            print("❌ 在本地 HTML 中未发现 class='ip-link' 的元素。")
            # 打印前 500 个字符看看 HTML 是否读取正确
            content = await page.content()
            print(f"📄 HTML 片段: {content[:500]}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
