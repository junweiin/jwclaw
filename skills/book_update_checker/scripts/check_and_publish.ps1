# Book Update Checker and Publisher
# This script checks WordPress for new books, compares with local database,
# updates books.txt, and runs the publish script.

param()

Write-Host "=" * 70
Write-Host "  Book Update Checker & Publisher"
Write-Host "=" * 70

# Configuration
$wordpress_url = "https://http561856124.wordpress.com/"
$local_db_url = "https://book.junwei.bid/?jwclaw"
$books_file = "C:\Users\jw\Desktop\aicode\code\发布助手\books.txt"
$publish_script = "C:\Users\jw\Desktop\aicode\code\发布助手\run.bat"

# Step 1: Check WordPress blog
Write-Host "`n[Step 1/5] Checking WordPress blog for updates..."
try {
    $wp_response = Invoke-WebRequest -Uri $wordpress_url -UseBasicParsing -TimeoutSec 30
    $wp_content = $wp_response.Content
    Write-Host "[OK] Successfully fetched WordPress content ($($wp_content.Length) bytes)"
    
    # Extract titles (simple regex)
    $title_matches = [regex]::Matches($wp_content, '<h[1-6][^>]*>(.*?)</h[1-6]>')
    $titles = $title_matches | ForEach-Object { $_.Groups[1].Value -replace '<[^>]+>', '' } | Where-Object { $_.Trim() }
    Write-Host "[INFO] Found $($titles.Count) headings in WordPress"
    
} catch {
    Write-Host "[ERROR] Failed to access WordPress: $_"
    exit 1
}

# Step 2: Get local book database
Write-Host "`n[Step 2/5] Fetching local book database..."
try {
    $local_response = Invoke-WebRequest -Uri $local_db_url -UseBasicParsing -TimeoutSec 30
    $local_content = $local_response.Content
    Write-Host "[OK] Successfully fetched local database ($($local_content.Length) bytes)"
    
} catch {
    Write-Host "[ERROR] Failed to access local database: $_"
    exit 1
}

# Step 3: Prepare data for LLM analysis
Write-Host "`n[Step 3/5] Preparing data for LLM comparison..."

# Save content to temporary files for LLM processing
$wp_temp = "$env:TEMP\wordpress_content.txt"
$local_temp = "$env:TEMP\local_database.txt"

$wp_content | Out-File $wp_temp -Encoding UTF8
$local_content | Out-File $local_temp -Encoding UTF8

Write-Host "[INFO] WordPress content saved to: $wp_temp"
Write-Host "[INFO] Local database saved to: $local_temp"
Write-Host "[INFO] Please use LLM to compare these files and identify new books"
Write-Host "[INFO] Expected output format: one book title per line in books.txt format"

# For now, we'll prompt user to manually review
Write-Host "`n[WARN] Automatic LLM comparison requires integration with jwclaw's LLM API"
Write-Host "[INFO] For now, please manually check the differences"
Write-Host "[INFO] Or configure LLM integration in the skill"

# Step 4: Update books.txt with new books (ONLY file to be modified)
Write-Host "`n[Step 4/5] Updating books.txt..."

if (Test-Path $books_file) {
    # Backup before modification
    $backup_file = $books_file + ".bak_" + (Get-Date -Format "yyyyMMdd_HHmmss")
    Copy-Item $books_file $backup_file -Force
    Write-Host "[OK] Backed up books.txt to: $backup_file"
    
    # Read current content
    $current_books = Get-Content $books_file -Raw
    Write-Host "[INFO] Current books.txt has $($current_books.Length) characters"
    
    # NOTE: In production, LLM should provide the new book list
    # For now, this is a placeholder showing the update process
    Write-Host "[INFO] To update: Replace content with new book list from LLM analysis"
    Write-Host "[INFO] Example format:"
    Write-Host "  Book Title 1"
    Write-Host "  Book Title 2"
    Write-Host "  Book Title 3"
    
    # Uncomment below when LLM integration is ready:
    # $new_books = "New Book 1`nNew Book 2"  # From LLM output
    # Set-Content $books_file $new_books -Encoding UTF8
    # Write-Host "[OK] books.txt updated with new books"
    
} else {
    Write-Host "[ERROR] books.txt not found at: $books_file"
    Write-Host "[INFO] Please ensure the file exists"
    exit 1
}

# Step 5: Execute publish script (READ ONLY - just run it)
Write-Host "`n[Step 5/5] Executing publish script..."

if (Test-Path $publish_script) {
    try {
        Write-Host "[INFO] Running: $publish_script"
        Write-Host "[INFO] Note: run.bat will be executed but NOT modified"
        Start-Process "cmd.exe" -ArgumentList "/c", "`"$publish_script`"" -Wait -NoNewWindow
        Write-Host "[OK] Publish script completed successfully"
    } catch {
        Write-Host "[ERROR] Failed to execute publish script: $_"
        exit 1
    }
} else {
    Write-Host "[ERROR] run.bat not found at: $publish_script"
    Write-Host "[INFO] Please ensure the publish script exists"
    exit 1
}

Write-Host "`n" + ("=" * 70)
Write-Host "  Book update check and publish process completed!"
Write-Host ("=" * 70)
Write-Host "`nNext steps:"
Write-Host "1. Review temporary files for WordPress vs Local DB comparison"
Write-Host "   - WordPress content: $wp_temp"
Write-Host "   - Local database: $local_temp"
Write-Host "2. Use LLM to analyze differences and identify new books"
Write-Host "3. Update books.txt with new book list (one per line)"
Write-Host "4. Run publish script again if books.txt was updated"
