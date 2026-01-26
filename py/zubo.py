import asyncio
from playwright.async_api import async_playwright
import re
import os
import time

async def get_real_content():
    async with async_playwright() as p:
        # 1. 尝试使用低负载模式
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = await context.new_page()

        # 2. 监听所有收到的网络响应 (寻找隐藏的数据文件)
        data_sources = []
        page.on("response", lambda response: data_sources.append(response.url) if ".txt" in response.url or ".m3u" in response.url else None)

        try:
            target_url = "https://iptv.cqshushu.com/index.php"
            print(f"🚀 访问目标 (缩短等待时间): {target_url}")
            
            # 使用 'commit' 模式，只要服务器有响应就立即开始，不再等 JS 运行完
            await page.goto(target_url, wait_until="commit", timeout=30000)
            
            # 手动等待一小会儿
            await asyncio.sleep(5)
            
            content = await page.content()
            
            # 3. 检查是否依然卡在验证
            if "请稍候" in content:
                print("⚠️ 仍然卡在验证页，尝试获取当前页面所有的链接文本...")
            
            # 4. 提取 IP (尝试更宽松的正则)
            ips = list(dict.fromkeys(re.findall(r"(?:\d{1,3}\.){3}\d{1,3}", content)))
            ips = [ip for ip in ips if not ip.startswith(('127.', '192.', '10.', '172.', '0.'))]

            # 5. 调试输出
            os.makedirs("debug", exist_ok=True)
            with open("debug/last_attempt.html", "w", encoding="utf-8") as f:
                f.write(content)
            
            print(f"📄 源码长度: {len(content)}")
            print(f"📡 嗅探到的潜在数据源: {data_sources}")
            print(f"✅ 找到 IP 数量: {len(ips)}")

            return ips

        except Exception as e:
            print(f"❌ 访问超时或失败，通常是 IP 被封。错误: {e}")
            return []
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(get_real_content())
