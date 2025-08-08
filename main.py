import os
from utils import EyxeduSession, write_playlist_file

session = EyxeduSession()
buffer = []

for page in range(1, session.total_pages() + 1):
    for title, ts_url, stuck in session.deal_page(page):
        if stuck:
            #print("🕐 正在等待解除频率限制…")
            # 卡住时，把缓存的全部写入文件，然后清空缓存
            for b_title, b_ts_url in buffer:
                write_playlist_file(b_title, b_ts_url)
            buffer.clear()
        else:
            print(f"✅ 已获取：{title} → {ts_url}")
            # 不卡住时，先缓存
            buffer.append((title, ts_url))

# 循环结束后，把剩余的缓存也写入文件
for b_title, b_ts_url in buffer:
    write_playlist_file(b_title, b_ts_url)
buffer.clear()

