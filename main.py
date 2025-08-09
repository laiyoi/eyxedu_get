import os
from utils import EyxeduSession, write_playlist_file

session = EyxeduSession()
buffer = []

#session.login(os.getenv("USERNAME"), os.getenv("PASSWORD"))
session.access_check()
pages = session.total_pages() + 1
for page in range(1, pages):
    for title, ts_url in session.deal_page(page):
        if ts_url:
            print(f"✅ 已获取：{title} → {ts_url}")
            # 不卡住时，先缓存
            buffer.append((title, ts_url))

        else:
            # 卡住时，把缓存的全部写入文件，然后清空缓存
            print(len(buffer), "个缓存的课程信息已写入文件")
            write_playlist_file(buffer)
            buffer.clear()
            

# 循环结束后，把剩余的缓存也写入文件
write_playlist_file(buffer)
buffer.clear()

