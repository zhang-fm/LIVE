import asyncio
import random
import time
from playwright.async_api import async_playwright
# 使用通用的 stealth_page 入口
from playwright_stealth import stealth_page

async def simulate_human_behavior(page):
    """模拟人类滚动，增加 mouseMoves 和 scrolls 计数"""
    print("正在模拟人类浏览行为...")
    for _ in range(random.randint(2, 4)):
        # 随机滚动位移
        scroll_y = random.randint(200, 500)
        await page.mouse.wheel(0, scroll_y)
        await asyncio.sleep(random.uniform(0.5, 1.5))
    
    # 模拟鼠标在页面中心附近晃动
    await page.mouse.move(random.randint(100, 500), random.randint(100, 500))

async def main():
    async with async_playwright() as p:
        # 1. 启动浏览器
        browser = await p.chromium.launch(headless=True)
        # 模拟真实的屏幕尺寸和 UA，这会影响生成的 paer_token
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1344, 'height': 840}
        )
        
        page = await context.new_page()
        # 2. 启用隐身模式，绕过 webdriver 检测
        await stealth_page(page)
        
        url = "https://iptv.cqshushu.com/"
        print(f"🚀 访问主页: {url}")
        
        try:
            # 访问主页并等待网络空闲
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(2)
            
            # 执行模拟动作（非常重要：影响 token 生成）
            await simulate_human_behavior(page)
            
            # 3. 定位所有的 IP 链接
            # 选择器针对你提供的 <a class="ip-link" ...>
            ip_links = await page.query_selector_all("a.ip-link")
            
            if not ip_links:
                print("❌ 未发现 IP 链接，可能页面未加载成功。")
                await page.screenshot(path="no_links_error.png")
                return

            print(f"✅ 发现 {len(ip_links)} 个 IP 节点。准备进入第一个节点的详情页...")

            # 4. 模拟真实点击并捕获跳转
            # 我们通过监听导航事件来处理点击跳转
            async with page.expect_navigation(wait_until="networkidle", timeout=60000):
                # 滚动到该元素以确保可见
                await ip_links[0].scroll_into_view_if_needed()
                # 模拟鼠标移动到元素中心并点击
                box = await ip_links[0].bounding_box()
                await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)

            # 5. 到达详情页，提取内容
            print(f"🎉 已成功跳转至详情页: {page.url}")
            
            # 保存截图以验证画面
            await page.screenshot(path="detail_success.png")
            
            # 提取详情页 HTML 源码
            detail_content = await page.content()
            with open("detail_page.txt", "w", encoding="utf-8") as f:
                f.write(detail_content)
            
            # 简单示例：搜索详情页中的所有 rtp/udp 链接
            raw_links = []
            # 这里可以根据详情页的具体标签修改
            all_text = await page.inner_text("body")
            urls = [] # 这里可以用正则提取具体地址
            
            print("任务完成，文件已保存。")

        except Exception as e:
            print(f"❌ 运行出错: {e}")
            await page.screenshot(path="crash_error.png")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
