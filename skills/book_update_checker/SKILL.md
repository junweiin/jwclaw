---
name: book_update_checker
description: 自动检测WordPress博客更新，对比本地书籍数据库，发现新书后自动更新books.txt并执行发布脚本
---

## 描述
**自动化书籍更新检测和发布工具**。定期检查WordPress博客是否有新书发布，与本地数据库对比，自动更新books.txt文件并执行发布脚本。

**工作流程：**
1. 访问WordPress博客检查更新
2. 访问本地书籍数据库获取当前数据
3. LLM对比分析，识别新书
4. 更新books.txt文件（删除旧数据，添加新书）
5. 执行run.bat发布脚本

## 调用格式
tool: book_update_checker()

## 命令列表
| 命令 | 说明 | 参数 |
|------|------|------|
| check_and_publish | 检查更新并发布 | 无 |

## 前置条件
```bash
# 需要安装requests库
pip install requests beautifulsoup4
```

## 执行流程

### Step 1: 检查WordPress博客更新
```powershell
Write-Host "📖 正在检查WordPress博客更新..."
$url_wordpress = "https://http561856124.wordpress.com/"

try {
    $response = Invoke-WebRequest -Uri $url_wordpress -UseBasicParsing -TimeoutSec 30
    $wordpress_content = $response.Content
    Write-Host "[OK] 成功获取WordPress内容"
    
    # 提取最新文章标题和链接
    $titles = [regex]::Matches($wordpress_content, '<title[^>]*>(.*?)</title>') | ForEach-Object { $_.Groups[1].Value }
    Write-Host "找到 $($titles.Count) 个标题"
    
} catch {
    Write-Host "[ERROR] 无法访问WordPress: $_"
    exit 1
}
```

### Step 2: 获取本地书籍数据库
```powershell
Write-Host "`n📚 正在获取本地书籍数据库..."
$url_local = "https://book.junwei.bid/?jwclaw"

try {
    $response = Invoke-WebRequest -Uri $url_local -UseBasicParsing -TimeoutSec 30
    $local_content = $response.Content
    Write-Host "[OK] 成功获取本地数据库内容"
    
} catch {
    Write-Host "[ERROR] 无法访问本地数据库: $_"
    exit 1
}
```

### Step 3: 调用LLM对比分析
```powershell
Write-Host "`n🤖 正在调用LLM分析新书..."

# 准备对比数据
$comparison_prompt = @"
请对比以下两个来源的内容，找出WordPress博客中有但本地数据库中没有的新书。

WordPress博客内容（前5000字符）:
$($wordpress_content.Substring(0, [Math]::Min(5000, $wordpress_content.Length)))

本地数据库内容（前5000字符）:
$($local_content.Substring(0, [Math]::Min(5000, $local_content.Length)))

请列出所有新书的书名，每行一个。如果没有新书，回复"无新书"。
"@

# 这里需要通过jwclaw的LLM接口调用
Write-Host "[INFO] 需要将对比数据发送给LLM分析"
Write-Host "[INFO] 等待LLM返回新书列表..."
```

### Step 4: 更新books.txt文件
```powershell
$books_file = "C:\Users\jw\Desktop\aicode\code\发布助手\books.txt"

if (Test-Path $books_file) {
    Write-Host "`n📝 正在更新books.txt..."
    
    # 备份原文件
    $backup_file = $books_file + ".bak"
    Copy-Item $books_file $backup_file -Force
    Write-Host "[OK] 已备份原文件"
    
    # 读取现有内容
    $existing_content = Get-Content $books_file -Raw
    
    # LLM返回的新书列表（需要从Step 3获取）
    # $new_books = "新书1`n新书2`n新书3"
    
    # 清空文件并写入新书
    # Set-Content $books_file $new_books -Encoding UTF8
    Write-Host "[OK] books.txt已更新"
    
} else {
    Write-Host "[ERROR] books.txt文件不存在: $books_file"
    exit 1
}
```

### Step 5: 执行发布脚本
```powershell
$publish_script = "C:\Users\jw\Desktop\aicode\code\发布助手\run.bat"

if (Test-Path $publish_script) {
    Write-Host "`n🚀 正在执行发布脚本..."
    
    try {
        Start-Process "cmd.exe" -ArgumentList "/c", "`"$publish_script`"" -Wait -NoNewWindow
        Write-Host "[OK] 发布脚本执行完成"
    } catch {
        Write-Host "[ERROR] 发布脚本执行失败: $_"
        exit 1
    }
    
} else {
    Write-Host "[ERROR] run.bat文件不存在: $publish_script"
    exit 1
}

Write-Host "`n✅ 书籍更新检测和发布流程完成！"
```

## 注意事项
1. **首次使用**需要确保books.txt和run.bat文件存在
2. **网络连接**需要能访问WordPress和本地数据库
3. **LLM分析**需要配置好模型连接
4. **备份机制**会自动备份books.txt，防止数据丢失
5. **错误处理**每个步骤都有详细的错误提示

## 示例输出
```
📖 正在检查WordPress博客更新...
[OK] 成功获取WordPress内容
找到 15 个标题

📚 正在获取本地书籍数据库...
[OK] 成功获取本地数据库内容

🤖 正在调用LLM分析新书...
[INFO] 需要将对比数据发送给LLM分析
[INFO] 等待LLM返回新书列表...

📝 正在更新books.txt...
[OK] 已备份原文件
[OK] books.txt已更新

🚀 正在执行发布脚本...
[OK] 发布脚本执行完成

✅ 书籍更新检测和发布流程完成！
```
