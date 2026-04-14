# skill: web_search

## 描述
使用搜索引擎搜索网络信息。可以搜索新闻、知识、实时信息等。返回搜索结果摘要。

## 调用格式
tool: web_search("搜索关键词")

参数说明：
- 搜索关键词：要搜索的内容，支持中文和英文

## 执行代码
```python
import subprocess
import sys
import json

try:
    # 获取搜索关键词
    query = args[0].strip() if args else ""
    
    if not query:
        result = "❌ 错误: 请提供搜索关键词"
    else:
        # 使用Python调用搜索引擎API或使用curl/wget
        # 这里使用一个简单的方案：调用bing搜索或duckduckgo
        
        try:
            import requests
            from urllib.parse import quote
            
            # 使用DuckDuckGo API（免费，无需密钥）
            search_url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1&skip_disambig=1"
            
            response = requests.get(search_url, timeout=10)
            data = response.json()
            
            # 解析结果
            abstract = data.get('Abstract', '')
            abstract_url = data.get('AbstractURL', '')
            heading = data.get('Heading', '')
            related_topics = data.get('RelatedTopics', [])[:5]  # 最多5个相关主题
            
            result_lines = [f"🔍 搜索结果: {query}", "=" * 50]
            
            if heading or abstract:
                if heading:
                    result_lines.append(f"\n📌 {heading}")
                if abstract:
                    result_lines.append(f"{abstract}")
                if abstract_url:
                    result_lines.append(f"\n🔗 来源: {abstract_url}")
            
            if related_topics:
                result_lines.append(f"\n📋 相关内容:")
                for i, topic in enumerate(related_topics, 1):
                    text = topic.get('Text', '')
                    url = topic.get('FirstURL', '')
                    if text and len(text) > 20:  # 过滤太短的内容
                        result_lines.append(f"\n{i}. {text[:200]}...")
                        if url:
                            result_lines.append(f"   🔗 {url}")
            
            if not heading and not abstract and not related_topics:
                result_lines.append("\n⚠️  未找到相关结果，请尝试其他关键词")
            
            result = "\n".join(result_lines)
            
        except ImportError:
            # 如果没有requests库，提供备选方案
            result = f"⚠️  需要安装requests库才能使用网络搜索\n\n请运行: pip install requests\n\n或者直接使用浏览器搜索: https://www.bing.com/search?q={quote(query)}"
        except Exception as e:
            result = f"❌ 搜索失败: {str(e)}\n\n提示: 请检查网络连接"
            
except Exception as e:
    result = f"❌ 执行出错: {str(e)}"
```
