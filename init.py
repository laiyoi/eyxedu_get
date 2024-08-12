import json, time, requests, asyncio, aiohttp
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from tqdm.asyncio import tqdm

save_path = Path("G:/网课")

url = "https://apppc.eyxedu.com/course-review"
with open("cookies.json", "r", encoding="utf-8") as f:
    cookies = json.load(f)

def get_pages(driver):
    pager = driver.find_element(By.CLASS_NAME, "el-pager")
    return int(pager.text[-2:])

def get_review_list(driver):
    review_list = driver.find_element(By.CLASS_NAME, "review-list")
    return review_list.find_elements(By.CLASS_NAME, "el-card.pointer.is-always-shadow")

def wait_for_content_load_in_menu(driver):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "el-loading-mask"))
    )
    time.sleep(0.07)

def turn_page(driver, page):
    page_box = driver.find_element(By.CLASS_NAME, "el-pagination__editor")
    numbox = page_box.find_element(By.TAG_NAME, "input")
    numbox.clear()
    numbox.send_keys(str(page))
    numbox.send_keys(Keys.RETURN)

def clean_filename(filename):
    # 替换不合法字符
    return filename.replace(":", "-").replace("/", "-").replace("\\", "-").replace("?", "").replace("\"", "").replace("<", "").replace(">", "").replace("|", "")

async def download_ts(url, filename, save_path):
    """异步下载.ts文件，带有进度条"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            print(f"Start to download {filename}")
            if response.status == 200:
                file_path = save_path / filename
                total_size = int(response.headers.get('content-length', 0))
                print(f"Downloading {filename} ({total_size} bytes)")
                with open(file_path, 'wb') as f, tqdm(total=total_size, unit='B', unit_scale=True, desc=filename, miniters=1) as pbar:
                    async for chunk in response.content.iter_chunked(1024):
                        f.write(chunk)
                        pbar.update(len(chunk))
                print(f"Download completed: {filename}")
            else:
                print(f"Failed to download {filename}, Status code: {response.status}")

def find_ts_url(driver):
    entries = driver.execute_script("""
        var entries = window.performance.getEntries();
        var urls = [];
        for (var i = 0; i < entries.length; i++) {
            if (entries[i].name.endsWith('.ts')) {
                urls.push(entries[i].name);
            }
        }
        return urls;
    """)
    if entries:
        return entries[0]
    else:
        return None

async def handle_page(driver, page, save_path, download_tasks):
    """处理每个页面的下载操作"""
    for i in range(len(get_review_list(driver))):
        wait_for_content_load_in_menu(driver)
        cards = get_review_list(driver)
        title = clean_filename(''.join(cards[i].text.split("\n")))  # 清理文件名
        cards[i].click()

        # 等待点击后的内容加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "video-wrap"))
        )

        # 获取.ts文件的URL
        ts_url = None
        while ts_url is None:
            ts_url = find_ts_url(driver)
            print(f"Found .ts URL in {title}:", ts_url)

        # 异步下载.ts文件，并立即开始执行
        filename = f"{title}.ts"
        download_tasks.append(asyncio.create_task(download_ts(ts_url, filename, save_path)))

        driver.back()
        wait_for_content_load_in_menu(driver)

        if page > 1:
            turn_page(driver, page)
            wait_for_content_load_in_menu(driver)

def main(driver, page_num, save_path):
    loop = asyncio.get_event_loop()
    download_tasks = []

    for page in range(1, page_num + 1):
        loop.run_until_complete(handle_page(driver, page, save_path, download_tasks))

        # 翻页
        if page < page_num:
            turn_page(driver, page + 1)
            wait_for_content_load_in_menu(driver)

    # 等待所有下载任务完成
    loop.run_until_complete(asyncio.gather(*download_tasks))

if __name__ == "__main__":
    driver = webdriver.Edge()
    driver.get(url)

    # 添加 cookies
    for cookie in cookies:
        cookie['sameSite'] = 'None' if cookie['sameSite'] == "unspecified" else cookie['sameSite']
        driver.add_cookie(cookie)

    # 重新加载页面
    driver.get(url)

    # 等待分页元素加载
    wait_for_content_load_in_menu(driver)

    # 获取页数
    page_num = get_pages(driver)

    main(driver, page_num, save_path)

    # 获取页面源代码并保存
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)

    driver.quit()
