import os
import json
import threading
import time
from pathlib import Path
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from utils import get_pages, get_review_list, wait_for_content_load_in_menu, turn_page, clean_filename, start_download_process, find_ts_url, write_playlist_file, get_page
import argparse

parser = argparse.ArgumentParser(description='下载亿云校视频或保存为m3u8播放列表.')

parser.add_argument('-l', "--listmode", action='store_true', default=False, help="启用播放列表模式")
parser.add_argument('-p', "--save_path", type=str, default='G:/网课',help="视频保存位置")
parser.add_argument('-s', "--subjects", type=str, default='',help="指定科目,使用'_'分割")
parser.add_argument('-k', "--keywords", type=str, default='',help="指定停止关键词,使用'_'分割")
parser.add_argument('-hl', "--headless", action='store_true', default=False, help="启用无头模式")

args = parser.parse_args()
save_path = Path(args.save_path)
STOP_KEYWORDS = args.keywords.split("_")
SUBJECTS = args.subjects.split("_")
PLAYLIST = args.listmode
HEADLESS = args.headless
print(f"subjects: {SUBJECTS}\nkeywords: {STOP_KEYWORDS}\nlistmode: {PLAYLIST}\nsave_path: {save_path}\nheadless: {HEADLESS}")

url = "https://apppc.eyxedu.com/course-review"
with open("cookies.json", "r", encoding="utf-8") as f:
    cookies = json.load(f)

if not os.path.exists("playlist.m3u8"):
    with open("playlist.m3u8", "w", encoding="utf-8") as f:
        f.write("#EXTM3U8\n")
with open("playlist.m3u8", "r", encoding="utf-8") as f:
    playlist = f.read()

def handle_page(driver, page, stop_event, processes):
    """处理每个页面的下载操作"""
    for i in range(len(get_review_list(driver))):
        if stop_event.is_set():
            print("Stopping due to keyword match.")
            break

        # 检查子进程数量
        while len(processes) >= 3:
            print("Too many processes. Waiting...")
            time.sleep(5)  # 等待 5 秒钟再检查
            # 清理完成的进程
            processes[:] = [p for p in processes if p.poll() is None]
            driver.refresh()
            wait_for_content_load_in_menu(driver)

        if get_page(driver) != page:
            turn_page(driver, page)
            wait_for_content_load_in_menu(driver)
        
        title = clean_filename(''.join(get_review_list(driver)[i].text.split("\n")))
        # 检查标题是否包含停止关键词
        if any(keyword in title and keyword !='' for keyword in STOP_KEYWORDS):
            print(f"Title contains stop keyword: {title}")
            stop_event.set()  # 设置停止标志
            break
        if any(subject in title and subject != '' for subject in SUBJECTS):
            continue
        if PLAYLIST and title in playlist: continue
        filename = f"{title}.ts"
        filepath = save_path / filename
        if os.path.exists(filepath) and not PLAYLIST:
            print(f"File {filename} already exists.")
            continue
        card = get_review_list(driver)[i]
        card.click()

        # 等待点击后的内容加载
        WebDriverWait(driver, 40).until(
            EC.presence_of_element_located((By.CLASS_NAME, "video-wrap"))
        )

        # 获取.ts文件的URL
        ts_url = None
        while ts_url is None:
            ts_url = find_ts_url(driver)
            print(f"Found .ts URL in {title}:", ts_url)
        if not ts_url.endswith(".ts"):
            filename = f"{title}.{ts_url.split('.')[-1]}"
            filepath = save_path / filename
        if os.path.exists(filepath) and not PLAYLIST:
            print(f"File {filename} already exists.")
            driver.back()
            continue
        if not PLAYLIST:
            # 启动子进程执行下载任务
            process = start_download_process(ts_url, filepath)
            processes.append(process)
        else:
            write_playlist_file(title, ts_url)

        driver.back()
        wait_for_content_load_in_menu(driver)

def main(driver, page_num):
    stop_event = threading.Event()  # 用于控制停止
    processes = []  # 用于跟踪子进程
    for page in range(1, page_num + 1):
        time1 = time.time()
        turn_page(driver, page)
        wait_for_content_load_in_menu(driver)
        if stop_event.is_set():
            print("Stopping due to keyword match.")
            break
        try:
            handle_page(driver, page, stop_event, processes)
            print(f"Page {page} processed in {time.time() - time1:.2f} seconds.")
        except TimeoutException:
            print(f"Timeout occurred on page {page}.")
            page = page - 1
            continue

    # 等待所有子进程完成
    print("Waiting for all download processes to complete.")
    for process in processes:
        process.wait()  # 等待每个子进程完成

if __name__ == "__main__":
    options = webdriver.EdgeOptions()
    if HEADLESS:
        options.add_argument('--headless')
    driver = webdriver.Edge(options=options)
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