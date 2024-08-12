# utils.py

import os
import re
import subprocess
import time
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

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

def find_ts_url(driver):
    # 确保页面和资源加载完成
    driver.refresh()
    time.sleep(2)  # 根据需要调整等待时间

    entries = driver.execute_script("""
        var entries = window.performance.getEntriesByType('resource');
        var urls = [];
        for (var i = 0; i < entries.length; i++) {
            var entry = entries[i];
            if (entry.name.endsWith('.ts')) {
                urls.push(entry.name);
            }
        }
        return urls;
    """)

    if entries:
        return entries[0]
    return None
