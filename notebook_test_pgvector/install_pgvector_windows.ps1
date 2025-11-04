# pgvector Installation Script for Windows
# Run this as Administrator: Right-click → Run with PowerShell (as Admin)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "pgvector Installation Script for Windows" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Find PostgreSQL installation
Write-Host "Step 1: Locating PostgreSQL installation..." -ForegroundColor Yellow

$possiblePaths = @(
    "C:\Program Files\PostgreSQL\16",
    "C:\Program Files\PostgreSQL\15",
    "C:\Program Files\PostgreSQL\14",
    "C:\Program Files\PostgreSQL\13",
    "C:\PostgreSQL\16",
    "C:\PostgreSQL\15",
    "C:\xampp\postgresql"
)

$PG_HOME = $null
foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $PG_HOME = $path
        Write-Host "✅ Found PostgreSQL at: $PG_HOME" -ForegroundColor Green
        break
    }
}

if (-not $PG_HOME) {
    Write-Host "❌ PostgreSQL installation not found!" -ForegroundColor Red
    Write-Host "Please specify your PostgreSQL installation path:" -ForegroundColor Yellow
    $PG_HOME = Read-Host "Enter path (e.g., C:\Program Files\PostgreSQL\16)"

    if (-not (Test-Path $PG_HOME)) {
        Write-Host "❌ Invalid path. Exiting." -ForegroundColor Red
        exit 1
    }
}

# Extract PostgreSQL version
$versionMatch = $PG_HOME -match "PostgreSQL[\/\\](\d+)"
if ($versionMatch) {
    $pgVersion = $Matches[1]
    Write-Host "PostgreSQL Version: $pgVersion" -ForegroundColor Cyan
} else {
    Write-Host "⚠️ Could not determine PostgreSQL version" -ForegroundColor Yellow
    $pgVersion = Read-Host "Enter PostgreSQL version (e.g., 16)"
}

Write-Host ""

# Step 2: Check if pgvector is already installed
Write-Host "Step 2: Checking if pgvector is already installed..." -ForegroundColor Yellow

$vectorDll = Join-Path $PG_HOME "lib\vector.dll"
$vectorControl = Join-Path $PG_HOME "share\extension\vector.control"

if ((Test-Path $vectorDll) -and (Test-Path $vectorControl)) {
    Write-Host "✅ pgvector files already exist!" -ForegroundColor Green
    Write-Host "Location: $vectorDll" -ForegroundColor Cyan

    $reinstall = Read-Host "Do you want to reinstall? (y/n)"
    if ($reinstall -ne "y") {
        Write-Host "Skipping installation. Proceeding to verification..." -ForegroundColor Yellow
        goto Verify
    }
}

Write-Host ""

# Step 3: Download pgvector
Write-Host "Step 3: Downloading pgvector..." -ForegroundColor Yellow
Write-Host "Please download the appropriate version manually from:" -ForegroundColor Cyan
Write-Host "https://github.com/pgvector/pgvector/releases" -ForegroundColor Cyan
Write-Host ""
Write-Host "Look for: pgvector-X.X.X-pg$pgVersion-windows-x64.zip" -ForegroundColor Yellow
Write-Host ""

$downloadPath = Read-Host "Enter the path to the downloaded ZIP file (or press Enter to skip)"

if ($downloadPath -and (Test-Path $downloadPath)) {
    Write-Host "✅ Found downloaded file: $downloadPath" -ForegroundColor Green

    # Extract ZIP
    $extractPath = Join-Path $env:TEMP "pgvector_extract"
    Write-Host "Extracting to: $extractPath" -ForegroundColor Cyan

    if (Test-Path $extractPath) {
        Remove-Item $extractPath -Recurse -Force
    }

    Expand-Archive -Path $downloadPath -DestinationPath $extractPath -Force

    # Copy files
    Write-Host ""
    Write-Host "Step 4: Installing pgvector files..." -ForegroundColor Yellow

    # Find vector.dll in extracted folder
    $vectorDllSource = Get-ChildItem -Path $extractPath -Filter "vector.dll" -Recurse | Select-Object -First 1
    $vectorControlSource = Get-ChildItem -Path $extractPath -Filter "vector.control" -Recurse | Select-Object -First 1
    $vectorSqlFiles = Get-ChildItem -Path $extractPath -Filter "vector--*.sql" -Recurse

    if ($vectorDllSource) {
        try {
            # Copy DLL
            $libPath = Join-Path $PG_HOME "lib"
            Copy-Item $vectorDllSource.FullName -Destination $libPath -Force
            Write-Host "✅ Copied vector.dll to $libPath" -ForegroundColor Green

            # Copy control file
            $extPath = Join-Path $PG_HOME "share\extension"
            if (-not (Test-Path $extPath)) {
                New-Item -Path $extPath -ItemType Directory -Force | Out-Null
            }

            Copy-Item $vectorControlSource.FullName -Destination $extPath -Force
            Write-Host "✅ Copied vector.control to $extPath" -ForegroundColor Green

            # Copy SQL files
            foreach ($sqlFile in $vectorSqlFiles) {
                Copy-Item $sqlFile.FullName -Destination $extPath -Force
                Write-Host "✅ Copied $($sqlFile.Name) to $extPath" -ForegroundColor Green
            }

            Write-Host ""
            Write-Host "✅ Installation successful!" -ForegroundColor Green

        } catch {
            Write-Host "❌ Installation failed: $_" -ForegroundColor Red
            Write-Host "Please run this script as Administrator" -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host "❌ Could not find vector.dll in extracted files" -ForegroundColor Red
        exit 1
    }

} else {
    Write-Host "⚠️ Manual installation required" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please follow these steps:" -ForegroundColor Cyan
    Write-Host "1. Download pgvector from: https://github.com/pgvector/pgvector/releases" -ForegroundColor White
    Write-Host "2. Extract the ZIP file" -ForegroundColor White
    Write-Host "3. Copy vector.dll to: $PG_HOME\lib\" -ForegroundColor White
    Write-Host "4. Copy vector.control and vector--*.sql to: $PG_HOME\share\extension\" -ForegroundColor White
    Write-Host "5. Restart PostgreSQL service" -ForegroundColor White
    Write-Host ""

    $continue = Read-Host "Have you completed the manual installation? (y/n)"
    if ($continue -ne "y") {
        exit 0
    }
}

Write-Host ""

# Step 5: Restart PostgreSQL service
:Verify
Write-Host "Step 5: Restarting PostgreSQL service..." -ForegroundColor Yellow

$pgServices = Get-Service -Name "*postgres*" -ErrorAction SilentlyContinue
if ($pgServices) {
    foreach ($service in $pgServices) {
        Write-Host "Found service: $($service.Name) - Status: $($service.Status)" -ForegroundColor Cyan

        $restart = Read-Host "Restart $($service.Name)? (y/n)"
        if ($restart -eq "y") {
            try {
                Restart-Service $service.Name -Force
                Write-Host "✅ Service restarted successfully" -ForegroundColor Green
            } catch {
                Write-Host "⚠️ Could not restart service. Please restart manually." -ForegroundColor Yellow
            }
        }
    }
} else {
    Write-Host "⚠️ No PostgreSQL service found. You may need to restart manually." -ForegroundColor Yellow
}

Write-Host ""

# Step 6: Verification
Write-Host "Step 6: Verification" -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To verify installation, run this SQL command:" -ForegroundColor Cyan
Write-Host ""
Write-Host "CREATE EXTENSION IF NOT EXISTS vector;" -ForegroundColor White
Write-Host "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';" -ForegroundColor White
Write-Host ""
Write-Host "Or run your Jupyter notebook: notebook_test_pgvector/rag_pgvector.ipynb" -ForegroundColor Cyan
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "✅ Script completed!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
