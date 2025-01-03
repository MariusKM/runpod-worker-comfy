param(
    [Parameter(Mandatory=$true)]
    [string]$Path,
    [Parameter(Mandatory=$false)]
    [ValidateSet('Creation', 'Modified')]
    [string]$TimeType = 'Modified',
    [Parameter(Mandatory=$false)]
    [int]$TimeGap = 60
)

$files = Get-ChildItem -Path $Path -Recurse -File | 
    Select-Object FullName, CreationTime, LastWriteTime |
    Sort-Object { if ($TimeType -eq 'Creation') { $_.CreationTime } else { $_.LastWriteTime } }

if (-not $files) {
    Write-Host "No files found in specified directory."
    exit
}

$earliest = $files[0]
$latest = $files[-1]
$previousTime = if ($TimeType -eq 'Creation') { $files[0].CreationTime } else { $files[0].LastWriteTime }
$timeGaps = @()

for ($i = 1; $i -lt $files.Count; $i++) {
    $currentTime = if ($TimeType -eq 'Creation') { $files[$i].CreationTime } else { $files[$i].LastWriteTime }
    $timeDiff = $currentTime - $previousTime
    
    if ($timeDiff.TotalMinutes -gt $TimeGap) {
        $timeGaps += [PSCustomObject]@{
            StartTime = $previousTime
            EndTime = $currentTime
            GapMinutes = [math]::Round($timeDiff.TotalMinutes, 2)
            BeforeFile = $files[$i-1].FullName
            AfterFile = $files[$i].FullName
        }
    }
    $previousTime = $currentTime
}

Write-Host "`nTimestamp Analysis Results ($TimeType Time)`n" -ForegroundColor Cyan
Write-Host "Earliest file:" -ForegroundColor Green
Write-Host "  Time: $(if ($TimeType -eq 'Creation') { $earliest.CreationTime } else { $earliest.LastWriteTime })"
Write-Host "  File: $($earliest.FullName)"

Write-Host "`nLatest file:" -ForegroundColor Green
Write-Host "  Time: $(if ($TimeType -eq 'Creation') { $latest.CreationTime } else { $latest.LastWriteTime })"
Write-Host "  File: $($latest.FullName)"

if ($timeGaps.Count -gt 0) {
    Write-Host "`nTime gaps larger than $TimeGap minutes:" -ForegroundColor Yellow
    foreach ($gap in $timeGaps) {
        Write-Host "`nGap of $($gap.GapMinutes) minutes"
        Write-Host "  From: $($gap.StartTime)"
        Write-Host "    File: $($gap.BeforeFile)"
        Write-Host "  To: $($gap.EndTime)"
        Write-Host "    File: $($gap.AfterFile)"
    }
}