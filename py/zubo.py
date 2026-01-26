import asyncio
from playwright.async_api import async_playwright
import re
import os

async def get_real_content():
    async with async_playwright() as p:
        # 1. 启动并完全隐藏自动化特征
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            accept_language="zh-CN,zh;q=0.9",
            viewport={'width': 1280, 'height': 800}
        )

        # 核心：注入脚本，确保 navigator.webdriver 为 false
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)

        page = await context.new_page()
        
        # 2. 尝试访问 index.php
        target_url = "https://iptv.cqshushu.com/index.php"
        print(f"🚀 访问目标: {target_url}")
        
        try:
            # 增加超时并模拟正常等待
            await page.goto(target_url, wait_until="networkidle", timeout=60000)
            
            # 3. 应对 JS 盾：等待 10 秒让其完成本地 Cookie 计算和重定向
            print("⏳ 正在处理 JS 校验，请稍候...")
            await page.wait_for_timeout(10000) 

            # 4. 获取最终渲染的内容
            content = await page.content()
            
            # 5. 调试输出与保存
            os.makedirs("debug", exist_ok=True)
            print(f"📄 源码长度: {len(content)}")
            
            # 提取 IP
            ips = list(dict.fromkeys(re.findall(r"(?:\d{1,3}\.){3}\d{1,3}", content)))
            # 过滤内网/本地 IP
            ips = [ip for ip in ips if not ip.startswith(('127.', '192.', '10.', '172.', '0.'))]
            
            print(f"✅ 找到 IP 列表: {ips}")

            # 保存源码供你下载检查
            with open("debug/index_source.html", "w", encoding="utf-8") as f:
                f.write(content)
            
            # 截图看一眼现在的页面长什么样
            await page.screenshot(path="debug/index_view.png")
            
            return ips

        except Exception as e:
            print(f"❌ 访问出错: {e}")
            return []
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(get_real_content())
