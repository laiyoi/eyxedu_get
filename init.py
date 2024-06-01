import json, time, requests, threading
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

save_path = Path("G:\网课")

url = "https://apppc.eyxedu.com/course-review"
with open("cookies.json", "r", encoding="utf-8") as f:
    cookies = json.load(f)

def get_pages(driver):
    pager = driver.find_element(By.CLASS_NAME, "el-pager")
    return int(pager.text[-2:])

# 在每个"review-list flex"元素中，找到所有class为"el-card pointer is-always-shadow"的元素，并点击它们
def get_review_list(driver):
    review_list = driver.find_element(By.CLASS_NAME, "review-list")
    return review_list.find_elements(By.CLASS_NAME, "el-card.pointer.is-always-shadow")

def wait_for_content_load_in_menu(driver):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "el-loading-mask"))
        )
    time.sleep(0.07)
    
def turn_page(driver, page):
    page_box = driver.find_element(
            By.CLASS_NAME, "el-pagination__editor"
        )
    numbox = page_box.find_element(By.TAG_NAME, "input")
    numbox.clear()
    numbox.send_keys(str(page))
    numbox.send_keys(Keys.RETURN)

def download_ts(url, name):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path / name, "wb") as f:
            f.write(response.content)
        print(f"Downloaded {url}")
    else:
        print(f"Failed to download {url}")

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

with open("index.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)

for page in range(1, page_num+1):
    for i in range(len(get_review_list(driver))):
        wait_for_content_load_in_menu(driver)
        cards = get_review_list(driver)
        title = ''.join(cards[i].text.split("\n"))
        cards[i].click()
        # 等待点击后的内容加载，可以增加等待条件
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "video-wrap"))
        )
        # 获取.ts文件的URL
        ts_url = None
        while ts_url == None:
            ts_url = find_ts_url(driver)
            print(f"Found .ts URL in {title}:", ts_url)
        download_ts(ts_url)
        #threads = []
        #for url in ts_url:
        #    t = threading.Thread(target=download_ts, args=(ts_url, f"{title[:-4]}.ts"))
        #    t.start()
        #    threads.append(t)
        #for t in threads:
        #    t.join()
        driver.back()
        wait_for_content_load_in_menu(driver)
        if page == 1: continue
        turn_page(driver, page)
        wait_for_content_load_in_menu(driver)              
    turn_page(driver, page+1)
    wait_for_content_load_in_menu(driver)


# 获取页面源代码并保存
with open("index.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)

driver.quit()
