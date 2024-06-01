import requests
from bs4 import BeautifulSoup

# 初始 URL
url = 'https://apppc.eyxedu.com'

# 获取页面源代码并保存
def save_page(page, i):
    with open(f"index{i}.html", "wb") as f:
        f.write(page)

# 创建一个 session 对象
session = requests.Session()

# 获取初始页面
for i in range(10):
    response = session.get(url)
    html_content = response.text
    save_page(response.content, i)

# 解析 HTML，找到目标元素
soup = BeautifulSoup(html_content, 'html.parser')
target_element = soup.find('a', {'id': 'target-element-id'})  # 修改选择器以匹配你的目标元素

if target_element:
    target_url = target_element.get('href')
    
    # 如果目标 URL 是相对路径，构建完整 URL
    if target_url and not target_url.startswith('http'):
        from urllib.parse import urljoin
        target_url = urljoin(initial_url, target_url)
    
    # 发送请求到目标 URL
    if target_url:
        response = session.get(target_url, allow_redirects=False)
        
        # 检查响应是否包含重定向
        if 300 <= response.status_code < 400:
            redirect_url = response.headers.get('Location')
            print(f'Redirect URL: {redirect_url}')
        else:
            print(f'Final URL: {response.url}')
else:
    print('Target element not found')
