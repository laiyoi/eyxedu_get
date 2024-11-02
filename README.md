# 免责声明
***本项目仅为下载工具，不提供登录权限、课程视频等内容。<br>
任何使用本项目下载、传播、售卖视频内容的行为，均与本项目无关！***
# eyxed get 亿云校视频批量下载器
看见牢周录屏27分钟所以做了一个批量下载器
# requirements
- python3.11.3
- selenium
# 使用方法
- 使用`editthiscookie`插件复制网页cookie后创建`cookies.json`，粘贴进去
- 运行init.py
  ```
  options:
  -h, --help            show this help message and exit
  -l, --listmode        启用播放列表模式
  -p SAVE_PATH, --save_path SAVE_PATH
                        视频保存位置
  -s SUBJECTS, --subjects SUBJECTS
                        指定科目,使用'_'分割
  -k KEYWORDS, --keywords KEYWORDS
                        指定停止关键词,使用'_'分割
  ```
# 已知问题
对于教室性能低下的大屏，可能因最小化浏览器窗口导致崩溃
# TODO List
- [x] 按页遍历
- [x] 下载
- [x] 分科目下载
- [x] 下载`.m3u8`播放列表
- [x] 播放列表自动排序
- [ ] 分时间下载
