import os, re
import threading
import json
import time
import subprocess
from pathlib import Path
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

save_path = Path("G:/网课")
url = "https://apppc.eyxedu.com/course-review"
with open("cookies.json", "r", encoding="utf-8") as f:
    cookies = json.load(f)

# 特定字符检查
STOP_KEYWORDS = ['期末试卷讲评']

def get_pages(driver):
    pager = driver.find_element(By.CLASS_NAME, "el-pager")
    return int(pager.text[6:])

def get_review_list(driver):
    review_list = driver.find_element(By.CLASS_NAME, "review-list")
    return review_list.find_elements(By.CLASS_NAME, "el-card.pointer.is-always-shadow")

def wait_for_content_load_in_menu(driver):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "el-loading-mask"))
    )
    time.sleep(0.3)

def turn_page(driver, page):
    page_box = driver.find_element(By.CLASS_NAME, "el-pagination__editor")
    numbox = page_box.find_element(By.TAG_NAME, "input")
    numbox.clear()
    numbox.send_keys(str(page))
    numbox.send_keys(Keys.RETURN)

def clean_filename(filename):
    # 匹配第一个冒号后的内容和日期时间
    match = re.match(r'^(.*?)(高中.*?)(\d{4}\.\d{2}\.\d{2})(\d{2}:\d{2}-\d{2}:\d{2})', filename)
    if match:
        subject_part = match.group(1).strip()
        date_part = match.group(3)
        time_part = match.group(4)

        # 拼接结果
        filename = f"{subject_part} {date_part} {time_part}"
        
    else:
        # 如果无法匹配，则返回原始文件名
        filename = filename
    return filename.replace(":", "-").replace("/", "-").replace("\\", "-").replace("?", "").replace("\"", "").replace("<", "").replace(">", "").replace("|", "")
def start_download_process(url, filepath):
    """启动新的终端执行下载任务"""
    python_exe = r'venv\Scripts\python.exe'  # 相对路径
    script_path = r'download_task.py'  # 相对路径
    command = [
        'cmd', '/c', python_exe, script_path, url, str(filepath)
    ]
    return subprocess.Popen(command, shell=True)  # 返回子进程对象

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

def handle_page(driver, page, stop_event, processes):
    """处理每个页面的下载操作"""
    
    for i in range(len(get_review_list(driver))):
        if stop_event.is_set():
            print("Stopping due to keyword match.")
            break
        
        # 检查子进程数量
        while len(processes) > 8:
            print("Too many processes. Waiting...")
            time.sleep(5)  # 等待 5 秒钟再检查

        wait_for_content_load_in_menu(driver)
        cards = get_review_list(driver)
        title = clean_filename(''.join(cards[i].text.split("\n")))
        filename = f"{title}.ts"
        filepath = save_path / filename
        if os.path.exists(filepath):
            continue
        
        # 检查标题是否包含停止关键词
        if any(keyword in title for keyword in STOP_KEYWORDS):
            print(f"Title contains stop keyword: {title}")
            stop_event.set()  # 设置停止标志
            break
        
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

        # 启动子进程执行下载任务
        process = start_download_process(ts_url, filepath)
        processes.append(process)

        driver.back()
        wait_for_content_load_in_menu(driver)

        if page > 1:
            turn_page(driver, page)
            wait_for_content_load_in_menu(driver)

def main(driver, page_num):
    stop_event = threading.Event()  # 用于控制停止
    processes = []  # 用于跟踪子进程
    for page in range(1, page_num + 1):
        turn_page(driver, page)
        wait_for_content_load_in_menu(driver)
        if stop_event.is_set():
            print("Stopping due to keyword match.")
            break
        try:
            handle_page(driver, page, stop_event, processes)
        except TimeoutException:
            print(f"Timeout occurred on page {page}.")
            page = page - 1
            continue

    # 等待所有子进程完成
    print("Waiting for all download processes to complete.")
    for process in processes:
        process.wait()  # 等待每个子进程完成

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

    main(driver, page_num)

    # 获取页面源代码并保存
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)

    driver.quit()
