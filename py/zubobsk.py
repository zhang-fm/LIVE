import asyncio
import os
import re
import threading
import http.server
import socketserver
from playwright.async_api import async_playwright

# 1. 定义一个简单的静态文件服务器
def start_local_server():
    os.chdir("data") # 进入 HTML 所在目录
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", 8000), handler) as httpd:
        print("📡 本地伪装服务器已启动: http://localhost:8000")
        httpd.serve_forever()

async def main():
    # 在后台线程启动服务器
    threading.Thread(target=start_local_server, daemon=True).start()
    await asyncio.sleep(2) # 等待服务器启动

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        page = await context.new_page()

        # 2. 访问本地伪装服务器
        print("🌐 访问伪装主页...")
        await page.goto("http://localhost:8000/shushu_home.html")
        await asyncio.sleep(2)

        # 3. 模拟点击
        ip_link = await page.query_selector("a.ip-link")
        if ip_link:
            print(f"✅ 找到 IP 链接，准备通过 HTTP 协议触发跳转...")
            try:
                # 监听跳转，wait_until 改为 commit 只要服务器响应就继续
                async with page.expect_navigation(wait_until="commit", timeout=60000):
                    await ip_link.click()
                
                print(f"🚀 跳转成功！当前地址: {page.url}")
                print("⏳ 正在等待目标页响应内容 (20s)...")
                await asyncio.sleep(20)
                
                title = await page.title()
                print(f"📑 最终页面标题: {title}")
                
                # 检查结果
                if "验证中" in title or "Just a moment" in title:
                    print("❌ 悲报：即便模拟了 HTTP 跳转，GitHub 的 IP 还是被 CF 拦住了。")
                else:
                    btn = page.get_by_role("button", name=re.compile("查看频道列表"))
                    if await btn.count() > 0:
                        print("🎉 突破成功！已看到‘查看频道列表’按钮。")
                
                await page.screenshot(path="final_result.png")
                
            except Exception as e:
                print(f"❌ 跳转超时或失败: {e}")
                await page.screenshot(path="timeout_error.png")
        else:
            print("❌ 未能在 HTML 中找到链接，请检查 shushu_home.html 内容")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
