param(
    [Parameter(Mandatory=$true)]
    [string]$sourceDirectory,
    
    [Parameter(Mandatory=$true)]
    [string]$destinationRoot
)

# Define the color mapping hashtable
$colorMap = @{
    '3350979' = 'INDIGO'
    '11212013' = 'ELECTRIC_PURPLE'
    '65378' = 'LIME_GREEN'
    '55512' = 'TURQUOISE'
    '16752128' = 'AMBER'
    '16765440' = 'GOLDEN_YELLOW'
    '2916897' = 'FOREST_GREEN'
    '16600577' = 'VERMILION'
    '5005441' = 'SLATE_BLUE'
    '8495811' = 'STEEL_BLUE'
    '8761788' = 'POWDER_BLUE'
    '15526887' = 'OFF_WHITE'
    '7495776' = 'DUSTY_ROSE'
    '7827809' = 'WARM_GRAY'
    '14199131' = 'GOLDEN_TAN'
    '15721872' = 'PALE_YELLOW'
    '5987425' = 'GUNMETAL_GRAY'
    '12498350' = 'LIGHT_TAUPE'
    '10521488' = 'MAUVE'
    '15321022' = 'MISTY_ROSE'
}

# Initialize counters
$processedCount = 0
$skippedCount = 0
$existingCount = 0

# Verify directories exist
if (-not (Test-Path $sourceDirectory)) {
    Write-Error "Source directory does not exist: $sourceDirectory"
    exit 1
}

# Create destination root if it doesn't exist
if (-not (Test-Path $destinationRoot)) {
    New-Item -ItemType Directory -Path $destinationRoot
}

Write-Host "Processing files from: $sourceDirectory"
Write-Host "Organizing into: $destinationRoot"
Write-Host "---"

# Get all PNG files in the directory and all subdirectories
Get-ChildItem -Path $sourceDirectory -Filter "*.png" -Recurse | ForEach-Object {
    $filename = $_.Name
    
    # Split the filename into components and remove empty elements
    $parts = ($filename -replace '\.png$', '') -split '_' | Where-Object { $_ -ne '' }
    
    if ($parts.Length -ge 6) {
        $vaseType = $parts[0]
        $token = $parts[1]
        $color1Code = $parts[2]
        $color2Code = $parts[3]
        $seed = $parts[4]
        $numberIdentifier = $parts[5]
        
        # Replace color codes with names if they exist in the mapping
        $color1Name = if ($colorMap.ContainsKey($color1Code)) { $colorMap[$color1Code] } else { $color1Code }
        $color2Name = if ($colorMap.ContainsKey($color2Code)) { $colorMap[$color2Code] } else { $color2Code }
        
        # Construct new filename (including the trailing underscore and .png extension)
        $newFilename = "{0}_{1}_{2}_{3}_{4}_{5}_.png" -f $vaseType, $token, $color1Name, $color2Name, $seed, $numberIdentifier
        
        # Construct new directory path: Color1/VaseType/
        $newDirectoryPath = Join-Path $destinationRoot $color1Name
        $newDirectoryPath = Join-Path $newDirectoryPath $vaseType
        
        # Create the directory structure if it doesn't exist
        if (-not (Test-Path $newDirectoryPath)) {
            New-Item -ItemType Directory -Path $newDirectoryPath -Force | Out-Null
        }
        
        # Construct the full destination path for the file
        $destinationPath = Join-Path $newDirectoryPath $newFilename
        
        # Check if file already exists
        if (Test-Path $destinationPath) {
            Write-Host "SKIPPING - File already exists:" -ForegroundColor Yellow
            Write-Host "Source: $($_.FullName)" -ForegroundColor Yellow
            Write-Host "Destination: $destinationPath" -ForegroundColor Yellow
            Write-Host "---"
            $existingCount++
        } else {
            # Show the operations that will be performed
            Write-Host "Processing file:"
            Write-Host "From: $($_.FullName)"
            Write-Host "To:   $destinationPath"
            Write-Host "---"
            
            # Add -WhatIf to test what would happen without actually moving files
            Copy-Item -Path $_.FullName -Destination $destinationPath #-WhatIf
            $processedCount++
        }
    }
    else {
        Write-Warning "Skipping '$filename' - doesn't match expected format"
        $skippedCount++
    }
}

# Print summary
Write-Host "`nSummary:" -ForegroundColor Cyan
Write-Host "Files processed: $processedCount" -ForegroundColor Green
Write-Host "Files skipped (existing): $existingCount" -ForegroundColor Yellow
Write-Host "Files skipped (invalid format): $skippedCount" -ForegroundColor Yellow

Write-Host "`nScript completed. Please review the -WhatIf output above and remove -WhatIf from Copy-Item to perform the actual file operations."