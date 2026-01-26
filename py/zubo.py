import asyncio
from playwright.async_api import async_playwright
import datetime
import os

async def run():
    async with async_playwright() as p:
        # 启动浏览器，使用真实浏览器指纹
        browser = await p.chromium.launch(headless=True)
        # 设置 context 模拟正常用户
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = await context.new_page()
        
        print("正在打开页面进行 JS 验证...")
        await page.goto("https://iptv.cqshushu.com/", wait_until="networkidle")
        
        # 等待页面重定向或 Cookie 生效，最多等 10 秒
        await page.wait_for_timeout(5000) 
        
        # 获取执行 JS 后的完整 HTML
        content = await page.content()
        
        # 保存内容
        os.makedirs("web_pages", exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
        filename = f"web_pages/home_{timestamp}.html"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"✅ 抓取成功！已保存至 {filename}")
        
        # 如果你想顺便提取 IP，可以继续在这里写正则
        # ips = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", content)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
