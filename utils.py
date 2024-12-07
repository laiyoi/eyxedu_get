# utils.py

import os
import re
import subprocess
import time
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

def get_pages(driver):
    pager = driver.find_element(By.CLASS_NAME, "el-pager")
    return int(pager.text[6:])

def get_review_list(driver):
    WebDriverWait(driver, 40).until(
        EC.presence_of_element_located((By.CLASS_NAME, "el-loading-mask"))
    )
    review_list = driver.find_element(By.CLASS_NAME, "review-list")
    cards = review_list.find_elements(By.CLASS_NAME, "el-card.pointer.is-always-shadow")
    try:
        cards[0].location
    except StaleElementReferenceException:
        cards = get_review_list(driver)
    return cards

def wait_for_content_load_in_menu(driver):
    WebDriverWait(driver, 40).until(
        EC.presence_of_element_located((By.CLASS_NAME, "el-pager"))
    )
    #time.sleep(0.05)

def turn_page(driver, page):
    page_box = WebDriverWait(driver, 40).until(
        EC.presence_of_element_located((By.CLASS_NAME, "el-pagination__editor"))
    )
    numbox = page_box.find_element(By.TAG_NAME, "input")
    numbox.clear()
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
        filename = f"{date_part} {time_part} {subject_part}"
        
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

def find_ts_url(driver)-> str:
    # 确保页面和资源加载完成
    driver.refresh()
    time.sleep(1.4)  # 根据需要调整等待时间
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "video-wrap"))
    )

    entries = driver.execute_script("""
        var entries = window.performance.getEntries();
        var urls = [];
        for (var i = 0; i < entries.length; i++) {
            if (entries[i].name.endsWith('.ts') || entries[i].name.endsWith('.mp4')) {
                urls.push(entries[i].name);
            }
        }
        return urls;
    """)


    if entries:
        return entries[0]
    return None

def sort_playlist_file(text: list):
    if not text: return []
    #将标题与url绑定之后按照标题中的日期排序
    playlist = {}
    for line in text:
        if line.startswith('#EXTINF'):
            title = line.split(',', 1)[1].strip()
            if title in playlist.keys(): continue
            playlist[title] = None
        elif line.startswith('http'):
            if line in playlist.values(): continue
            playlist[list(playlist.keys())[-1]] = line
    sorted_playlist = sorted(playlist.items(), key=lambda x: x[0], reverse=True)
    return ['#EXTM3U8\n'] + ['#EXTINF:-1,' + title + '\n' + str(url) for title, url in sorted_playlist]

def write_playlist_file(title, ts_url):
    if not os.path.exists("playlist.m3u8"):
        with open("playlist.m3u8", "w", encoding="utf-8") as f:
            f.write("#EXTM3U8\n")
    with open(f"playlist.m3u8", "r", encoding="utf-8") as f:
        text = f.readlines()
    text.append(f'#EXTINF:-1,{title}\n')
    text.append(f'{ts_url}\n')
    text = sort_playlist_file(text)
    with open(f"playlist.m3u8", "w", encoding="utf-8") as f:
        f.writelines(text)

def get_page(driver):
    return int(driver.find_element(By.CLASS_NAME, "el-pager").find_element(By.CLASS_NAME, "number.active").text)