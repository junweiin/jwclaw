---
name: news
description: "获取最新新闻资讯。支持查看科技、财经、国内、国际等多个类别的新闻。数据来自 RSS 订阅源，无需网络搜索 API。"
---

# 新闻资讯获取

## 描述
轻量级本地新闻聚合器，通过 RSS 订阅源获取最新新闻。无需外部搜索 API，适合获取各领域的最新资讯。

## 支持的新闻类别

- **tech** - 科技新闻
- **finance** - 财经新闻  
- **domestic** - 国内新闻
- **international** - 国际新闻
- **all** - 综合新闻（默认）

## 调用格式

tool: news("类别")

## 执行代码
```python
import json
from urllib.request import urlopen, Request
from urllib.error import URLError
from xml.etree import ElementTree as ET
from datetime import datetime
import time

# 内置 RSS 源
RSS_SOURCES = {
    "tech": [
        ("IT之家", "https://www.ithome.com/rss/"),
        ("Solidot", "https://www.solidot.org/index.rss"),
    ],
    "finance": [
        ("新浪财经", "https://rss.sina.com.cn/finance/stock/marketresearch.xml"),
        ("东方财富", "https://rss.cnfol.com/stock.xml"),
    ],
    "domestic": [
        ("澎湃新闻", "https://www.thepaper.cn/rss.xml"),
        ("网易新闻", "https://news.163.com/special/00011K6L/rss_newstop.xml"),
    ],
    "international": [
        ("BBC 中文", "http://feeds.bbci.co.uk/zhongwen/simp/rss.xml"),
    ],
    "all": [
        ("澎湃新闻", "https://www.thepaper.cn/rss.xml"),
        ("IT之家", "https://www.ithome.com/rss/"),
        ("新浪财经", "https://rss.sina.com.cn/finance/stock/marketresearch.xml"),
    ]
}

def fetch_rss(title, url, timeout=5):
    """获取单个 RSS 源"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
        }
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout) as response:
            data = response.read()
            
        # 解析 XML
        root = ET.fromstring(data)
        
        # 处理命名空间
        ns = {'content': 'http://purl.org/rss/1.0/modules/content/'}
        
        items = []
        # 查找 item 元素
        for item in root.findall('.//item'):
            title_elem = item.find('title')
            link_elem = item.find('link')
            desc_elem = item.find('description')
            pub_date = item.find('pubDate')
            
            if title_elem is not None and title_elem.text:
                items.append({
                    'title': title_elem.text.strip(),
                    'link': link_elem.text.strip() if link_elem is not None and link_elem.text else '',
                    'desc': desc_elem.text.strip()[:100] + '...' if desc_elem is not None and desc_elem.text and len(desc_elem.text) > 100 else (desc_elem.text.strip() if desc_elem is not None and desc_elem.text else ''),
                    'source': title,
                    'time': pub_date.text[:16] if pub_date is not None and pub_date.text else ''
                })
                if len(items) >= 3:  # 每个源最多取 3 条
                    break
        return items
    except Exception as e:
        return []  # 静默失败，不显示错误

# 获取查询参数
query = args[0].strip().lower() if args else "all"

# 映射别名
CATEGORY_MAP = {
    "科技": "tech", "tech": "tech", "technology": "tech",
    "财经": "finance", "finance": "finance", "经济": "finance", "股票": "finance",
    "国内": "domestic", "domestic": "domestic", "中国": "domestic",
    "国际": "international", "international": "international", "国外": "international", "世界": "international",
    "全部": "all", "all": "all", "综合": "all", "新闻": "all"
}

category = CATEGORY_MAP.get(query, "all")
sources = RSS_SOURCES.get(category, RSS_SOURCES["all"])

# 获取新闻
all_news = []
for source_name, source_url in sources:
    news_items = fetch_rss(source_name, source_url)
    all_news.extend(news_items)
    time.sleep(0.3)  # 短暂延迟，避免请求过快

# 按时间排序并限制数量
all_news = all_news[:10]  # 最多显示 10 条

# 生成结果
if all_news:
    lines = [f"📰 最新新闻 ({category.upper()})", "=" * 50, ""]
    for i, news in enumerate(all_news, 1):
        lines.append(f"{i}. {news['title']}")
        if news['desc']:
            lines.append(f"   {news['desc']}")
        if news['time']:
            lines.append(f"   🕐 {news['time']}")
        lines.append(f"   📎 {news['source']}")
        lines.append("")
    result = "\n".join(lines)
else:
    result = """⚠️ 暂时无法获取新闻

可能原因：
- 网络连接问题
- RSS 源暂时不可用

建议：
1. 检查网络连接
2. 稍后重试
3. 直接访问新闻网站查看"""
```
