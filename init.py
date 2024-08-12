import json
import time
import subprocess, asyncio
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

save_path = Path("G:/网课")

url = "https://apppc.eyxedu.com/course-review"
til = ""
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
    time.sleep(0.09)

def turn_page(driver, page):
    page_box = driver.find_element(By.CLASS_NAME, "el-pagination__editor")
    numbox = page_box.find_element(By.TAG_NAME, "input")
    numbox.clear()
    numbox.send_keys(str(page))
    numbox.send_keys(Keys.RETURN)

def clean_filename(filename):
    # 替换不合法字符
    return filename.replace(":", "-").replace("/", "-").replace("\\", "-").replace("?", "").replace("\"", "").replace("<", "").replace(">", "").replace("|", "")

def start_download_process(url, filename, save_path):
    """启动新的终端执行下载任务"""
    command = [
        'cmd', '/c', r'venv\Scripts\python.exe', 'download_task.py', url, filename, str(save_path)
    ]
    subprocess.Popen(command, shell=True)

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

async def handle_page(driver, page, save_path):
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

        # 启动新的终端进行下载
        filename = f"{title}.ts"
        print(f"Starting download for {filename}")  # 调试信息
        start_download_process(ts_url, filename, save_path)

        driver.back()
        wait_for_content_load_in_menu(driver)

        if page > 1:
            turn_page(driver, page)
            wait_for_content_load_in_menu(driver)

def main(driver, page_num, save_path):
    for page in range(1, page_num + 1):
        print(f"Handling page {page}")  # 调试信息
        asyncio.run(handle_page(driver, page, save_path))

        # 翻页
        if page < page_num:
            turn_page(driver, page + 1)
            wait_for_content_load_in_menu(driver)

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
