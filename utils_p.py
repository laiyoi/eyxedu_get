# utils.py

import os
import re
import threading
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

def get_pages(page):
    pager = page.query_selector(".el-pager")
    return int(pager.text_content()[6:])

def get_review_list(page):
    page.wait_for_selector(".el-loading-mask", timeout=40000)
    review_list = page.query_selector(".review-list")
    cards = review_list.query_selector_all(".el-card.pointer.is-always-shadow")
    try:
        cards[0].bounding_box()
    except Exception:
        cards = get_review_list(page)
    return cards

def wait_for_content_load_in_menu(page):
    page.wait_for_selector(".el-pager", timeout=40000)
    #time.sleep(0.05)

def turn_page(page, page_num):
    page_box = page.wait_for_selector(".el-pagination__editor", timeout=40000)
    numbox = page_box.query_selector("input")
    numbox.fill("")
    numbox.fill(str(page_num))
    numbox.press("Enter")

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

def find_ts_url(page)-> str:
    # 确保页面和资源加载完成
    page.reload()
    time.sleep(0.4)  # 根据需要调整等待时间
    page.wait_for_selector(".video-wrap", timeout=10000)

    entries = page.evaluate("""
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

def get_page(page):
    return int(page.query_selector(".el-pager .number.active").text_content())
