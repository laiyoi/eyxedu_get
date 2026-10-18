#!/bin/bash
echo '[
  {
    "title": "高二语文：习题课",
    "id": 42868,
    "time": "2025.07.16 15-07-16-10",
    "url": "https://cdn-gaoxin02.eduzhida.com/vodfiles/sharefiles/9680dfaf760a05410176d0c9694128e1/s/202507/16161203/ynfz6_18752181_24630107.ts"
  },
  {
    "title": "高二历史：汉统一多民族封建国家的巩固",
    "id": 42866,
    "time": "2025.07.16 13-57-15-00",
    "url": "https://cdn-gaoxin02.eduzhida.com/vodfiles/sharefiles/9680dfaf760a05410176d0c9694128e1/s/202507/16150303/mqbf_18751336_24629265.ts"
  }
]' > lesson.json

echo "JSON文件生成完成！"
ls -l *.json