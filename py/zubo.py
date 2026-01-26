import asyncio
from playwright.async_api import async_playwright
import re

async def get_real_content():
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 ...")
        page = await context.new_page()
        
        # 访问首页
        await page.goto("https://iptv.cqshushu.com/", wait_until="networkidle")
        
        # 关键：等待 5-10 秒让 JS 盾完成验证并重定向
        await page.wait_for_timeout(8000) 
        
        # 此时获取的内容才是绕过验证后的真实网页
        content = await page.content()
        
        # 提取 IP (沿用你之前的正则)
        ips = list(dict.fromkeys(re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", content)))
        print(f"找到 IP 列表: {ips}")
        
        await browser.close()
        return ips

if __name__ == "__main__":
    # 使用 asyncio 运行
    ips = asyncio.run(get_real_content())
    # 接下来跑你原来的扫描端口逻辑...
