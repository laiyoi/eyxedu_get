import json, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

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
        EC.presence_of_element_located((By.CLASS_NAME, "el-card.pointer.is-always-shadow"))
        )
    time.sleep(0.1)
    
def turn_page(driver, page):
    page_box = driver.find_element(
            By.CLASS_NAME, "el-pagination__editor"
        )
    numbox = page_box.find_element(By.TAG_NAME, "input")
    numbox.clear()
    numbox.send_keys(str(page))
    numbox.send_keys(Keys.RETURN)

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
        get_review_list(driver)[i].click()
        # 等待点击后的内容加载，可以增加等待条件
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "video-wrap"))
        )
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
