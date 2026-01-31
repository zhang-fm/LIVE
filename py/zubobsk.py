import asyncio
import random
import time
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def simulate_human_click(page, selector):
    # 获取元素位置
    element = await page.wait_for_selector(selector)
    box = await element.bounding_box()
    
    # 模拟鼠标轨迹移动到元素中心
    if box:
        x = box['x'] + box['width'] / 2
        y = box['y'] + box['height'] / 2
        # 分几步移动，模拟人类手感
        await page.mouse.move(x - 50, y - 50)
        await asyncio.sleep(0.5)
        await page.mouse.move(x, y, steps=10)
        await asyncio.sleep(0.2)
        await page.mouse.click(x, y)
        print(f"✅ 模拟点击完成: {selector}")

async def main():
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=True) # GitHub Actions 必须用无头模式
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1344, 'height': 840} # 匹配你链接里的屏幕尺寸
        )
        
        page = await context.new_page()
        # 绕过指纹检测
        await stealth_async(page)
        
        # 1. 访问主页
        url = "https://iptv.cqshushu.com/" # 替换为实际入口地址
        print(f"正在访问入口页: {url}")
        await page.goto(url, wait_until="networkidle")
        
        # 模拟一些随机滚动，增加 mouseMoves 计数
        await page.mouse.wheel(0, 500)
        await asyncio.sleep(1)
        
        # 2. 定位并点击 IP 链接
        # 这里用 class 和 text 组合定位，更加稳健
        ip_selector = "a.ip-link" 
        
        # 获取所有 IP 链接并点击第一个（或者你可以循环点击）
        links = await page.query_selector_all(ip_selector)
        if links:
            print(f"找到 {len(links)} 个 IP 链接，准备进入详情页...")
            
            # 捕获点击后产生的新请求或页面跳转
            async with page.expect_navigation(wait_until="networkidle", timeout=60000):
                await simulate_human_click(page, ip_selector)
            
            # 3. 进入详情页后，抓取内容
            print(f"成功进入详情页: {page.url}")
            
            # 打印详情页标题或内容作为验证
            content = await page.content()
            with open("detail_page.html", "w", encoding="utf-8") as f:
                f.write(content)
            
            # 也可以在这里提取具体的播放链接（如 m3u 文本）
            # play_links = await page.locator("text=http").all_inner_texts()
            # print(play_links)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
