# ---------------------------------------------------------------------------
# SOURCEMAP FORENSICS PRO: THE COMPLETE AUDIT TOOL (DYNAMIC & DEEP)
# ---------------------------------------------------------------------------

# 1. DYNAMIC FILE SELECTION
$availableMaps = Get-ChildItem -Filter "*.map"
if ($availableMaps.Count -gt 0) {
    Write-Host "[?] Detected .map files in this directory:" -ForegroundColor Cyan
    $availableMaps | ForEach-Object { Write-Host "  -> $($_.Name)" }
}

$jsMapFile = Read-Host "`n[>] Enter the full name of the .js.map file"

if (-not (Test-Path $jsMapFile)) {
    Write-Error "File '$jsMapFile' not found."
    exit
}

Write-Host "`n[+] Initializing Deep Scan: $jsMapFile" -ForegroundColor Cyan
Write-Host "[+] Parsing JSON structure... (Required for File Tree/Source Code check)" -ForegroundColor Gray

# 2. JSON STRUCTURE EXTRACTION (The "URL of the path" part)
try {
    $mapContent = Get-Content $jsMapFile -Raw
    $mapJson = $mapContent | ConvertFrom-Json
    $originalFiles = $mapJson.sources
    
    # Check for Embedded Source Code (Major severity booster)
    $isSourceExposed = $null -ne $mapJson.sourcesContent
} catch {
    Write-Host "[!] Warning: JSON parsing failed. File might be too large for RAM. Continuing with Regex only..." -ForegroundColor Yellow
    $originalFiles = @()
    $isSourceExposed = "Unknown"
}

# 3. DEFINE SEARCH PATTERNS
$routePattern  = '(/\w+)?/(api|internal|admin|debug|config|v1|v2|v3|graphql|gql|swagger|docs|test|dev|stg|prod|ws|rpc)/[^"\\\s]+'
$cloudPattern  = 'https?://[a-zA-Z0-9.-]+\.(firebaseio|amazonaws|googleapis|azure|herokudns|cloudfront)\.com[^"\\\s]*'
$secretPattern = '(key|secret|token|auth|password|credential|bearer)\s*[:=]\s*["''][^"'']{4,64}["'']'
$logicPattern  = '(isAdmin|isAuthorized|hasPermission|userRole|enableDebugMode)\s*[:=]\s*(true|false|1|0)'
$todoPattern   = '//\s*(TODO|FIXME|TEMP|DEBUG|BYPASS|HACK):.*'

# 4. EXECUTE EXTRACTION
Write-Host "[+] Running Regex Scan for High-Impact Leaks..." -ForegroundColor Cyan

$allPaths = Select-String -Path $jsMapFile -Pattern "$routePattern|$cloudPattern" -AllMatches | 
            ForEach-Object { $_.Matches | ForEach-Object { $_.Value } } | Sort-Object -Unique

$secrets  = Select-String -Path $jsMapFile -Pattern $secretPattern -AllMatches | 
            ForEach-Object { $_.Matches | ForEach-Object { $_.Value } } | Sort-Object -Unique

$logic    = Select-String -Path $jsMapFile -Pattern "$logicPattern" -AllMatches | 
            ForEach-Object { $_.Matches | ForEach-Object { $_.Value } } | Sort-Object -Unique

$todos    = Select-String -Path $jsMapFile -Pattern $todoPattern -AllMatches | 
            ForEach-Object { $_.Matches | ForEach-Object { $_.Value } } | Sort-Object -Unique

# 5. GENERATE THE SUMMARY
Write-Host "`n====================================================" -ForegroundColor Yellow
Write-Host "                ANALYSIS SUMMARY                    " -ForegroundColor Yellow
Write-Host "====================================================" -ForegroundColor Yellow
Write-Host "Original Source Files (Tree):      $($originalFiles.Count)"
Write-Host "Internal/API Endpoints found:      $($allPaths.Count)"
Write-Host "Potential Hardcoded Secrets:       $($secrets.Count)"
Write-Host "Privilege/Admin Logic Flags:       $($logic.Count)"
Write-Host "Developer Notes (TODO/DEBUG):      $($todos.Count)"
Write-Host "Embedded Source Code Leaked:       $isSourceExposed"
Write-Host "----------------------------------------------------`n"

if ($isSourceExposed -eq $true) {
    Write-Host "!!! ALERT: FULL ORIGINAL SOURCE CODE IS RECOVERABLE !!!" -ForegroundColor Red -BackgroundColor Black
    Write-Host "This bypasses almost all exclusions regarding 'Theoretical' issues.`n"
}

Write-Host "[!] SENSITIVE PATHS (REPRESENTATIVE):" -ForegroundColor Magenta
$allPaths | Where-Object { $_ -match "admin|internal|config|debug" } | Select-Object -First 5 | ForEach-Object { Write-Host " -> $_" }

if ($originalFiles.Count -gt 0) {
    Write-Host "`n[!] CRITICAL SOURCE FILES (PROJECT STRUCTURE):" -ForegroundColor Cyan
    $originalFiles | Where-Object { $_ -match "auth|admin|config|env" } | Select-Object -First 5 | ForEach-Object { Write-Host " [FILE] $_" }
}

# 6. EXPORT RESULTS
$originalFiles | Out-File -FilePath "audit_file_tree.txt"
$allPaths      | Out-File -FilePath "audit_endpoints.txt"
$secrets       | Out-File -FilePath "audit_secrets.txt"
$todos         | Out-File -FilePath "audit_comments.txt"

Write-Host "`n[+] Audit results saved to your current folder." -ForegroundColor Green