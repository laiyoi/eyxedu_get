from datetime import datetime
import requests
import json, time, os
from dotenv import load_dotenv

class EyxeduSession(requests.Session):
    
    def __init__(self):
        super().__init__()
        load_dotenv()
        self.phone = os.getenv("PHONE_NUMBER")
        self.password = os.getenv("PASSWORD")
        self.skip = os.getenv("SKIP_LIST", "true") == "true"

        self.headers.update(self.load_headers())
        try:
            with open("playlist.m3u8", "r", encoding="utf-8") as f:
                self.existing_titles = {line.strip().split(',')[1] for line in f if line.strip() and line.startswith("#EXTINF")}
        except FileNotFoundError:
            self.existing_titles = set()

    def load_headers(self):
        if os.path.exists("cookies.json"):
            with open("cookies.json", "r", encoding="utf-8") as f:
                return json.load(f)[0]
        else:
            self.login()
            return self.load_headers()
        
    def login(self):
        url = 'https://apppc.eyxedu.com/prod-api/bsyx/api/loginByPhone'
        data = {"phone": self.phone, "password": self.password, "rememberMe": "flase"}
        resp = self.post(url, data=data)
        print(resp.json())
        cookies = {}
        cookies['ids'] = str(resp.json()['data']['schools'][0]['ids'])
        cookies['token'] = resp.json()['data']['token']
        with open("cookies.json", "w", encoding="utf-8") as f:
            json.dump([cookies], f, ensure_ascii=False, indent=4)

    def access_check(self):
        if self.total_pages(): return True
        else:
            self.login()
            self.headers.update(self.load_headers())
            self.access_check()


    def get_lessons(self, page):
        url = "https://apppc.eyxedu.com/prod-api/bsyx/api/historySchedule"
        data = {"page": page, "limit": 12}
        try:
            resp = self.post(url, data=data)
        except requests.exceptions.RequestException as e:
            print(f"请求异常: {e}")
            return self.get_lessons(page)
        return resp.json()['data']
    
    def get_ts_url(self, course_id) -> str: 
        url = f"https://apppc.eyxedu.com/prod-api/bsyx/api/lookBack"
        data = {"courseId": course_id}
        try:
            resp = self.post(url, data=data)
        except requests.exceptions.RequestException as e:
            print(f"请求异常: {e}")
            return None
        
        res_json = resp.json()
        if res_json['code'] == 403:
            self.access_check()
            return self.get_ts_url(course_id)

        return res_json['data']['videoUrl'] if res_json['code'] != 500 else None

    def total_pages(self):
        url = "https://apppc.eyxedu.com/prod-api/bsyx/api/historySchedule"
        data = {"page": 1, "limit": 12}
        resp = self.post(url, data=data)
        return int(resp.json()['total']) // 12 + 1 if resp.json()['code'] == 200 else None
    
    def deal_page(self, page):
        lessons = self.get_lessons(page)
        for lesson in lessons:
            title = retitle(lesson)

            # 如果标题已存在，就跳过，不请求接口
            if title in self.existing_titles and self.skip:
                print(f"已存在，跳过：{title}")
                continue
            # 重试机制在这里
            while True:
                ts_url = self.get_ts_url(lesson["courseId"])
                if ts_url:
                    if ts_url.endswith('m3u8'):
                        ts_url = ts_url.rstrip('m3u8') + 'ts'
                    yield title, ts_url, lesson["courseId"]
                    break
                else:
                    print(f"请求过于频繁，等待中...（课程: {title}）")
                    yield title, None, lesson["courseId"] # 告诉外部现在卡住了，ts_url没拿到
                    time.sleep(5)

def parse_date(title):
    # 找出日期时间部分，格式类似 "2025.06.17 09-02-09-50"
    # 假设它在title开头，或者固定位置，先提取出这部分：
    # 这里假设日期时间是title开头的17个字符（yyyy.mm.dd HH-MM-SS-SS）
    dt_str = title[:22]
    # 分割日期和时间
    date_str, time_str = dt_str.split(' ')
    year, month, day = map(int, date_str.split('.'))
    h1, m1, s1, s2 = map(int, time_str.split('-'))
    return (year, month, day, h1, m1, s1, s2)

def format_timestamp_range(start_ts: int, end_ts: int) -> str:
    start_dt = datetime.fromtimestamp(start_ts)
    end_dt = datetime.fromtimestamp(end_ts)
    return start_dt.strftime("%Y.%m.%d %H-%M") + "-" + end_dt.strftime("%H-%M")

def retitle(lesson):
        title = lesson["courseTitle"]
        time = format_timestamp_range(lesson["startTime"], lesson["endTime"])
        return f"{time} {title}"

def sort_playlist_file(text):
    playlist = []
    title = None
    for line in text:
        line = line.strip()
        if line.startswith('#EXTINF'):
            title = line.split(',', 1)[1]
        elif title and line and not line.startswith('#'):
            playlist.append((title, line))
            title = None
    seen = set()
    unique = []
    for t, u in playlist:
        if t not in seen:
            unique.append((t, u))
            seen.add(t)
    unique.sort(key=lambda x: parse_date(x[0]), reverse=True)
    lines = ['#EXTM3U8\n'] + [f'#EXTINF:-1,{t}\n{u}\n' for t, u in unique]
    return lines

def write_playlist_file(lesson: list[tuple[str, str]]):
    filename = "playlist.m3u8"
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            f.write("#EXTM3U8\n")
    
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    for title, ts_url, _ in lesson:
        # 追加新的内容
        lines.append(f'#EXTINF:-1,{title}\n')
        lines.append(f'{ts_url}\n')
    
    # 调用排序函数
    sorted_lines = sort_playlist_file(lines)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(sorted_lines)

def write_json(lesson: list[tuple[str, str]]):
    data = []
    if os.path.exists('lesson.json'):
        with open("lesson.json", "r", encoding='utf-8') as f:
            data = json.load(f)

    for title, ts_url, id in lesson:
        lesson = {
            "title": title.split(' ')[2],
            'id': id,
            "time": ' '.join(title.split(' ')[:2]),
            "url": ts_url
        }
        data.append(lesson)
    with open("lesson.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


