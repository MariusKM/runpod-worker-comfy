# Get all folders in the current directory
$folders = Get-ChildItem -Directory

# Loop through each folder
foreach ($folder in $folders) {
    $folderName = $folder.Name
    
    # Construct and execute the aws s3 sync command for each folder
    $command = "aws s3 sync s3://jasper-250-runpod-staging-external-service-bucket/12-24/$folderName/ .\$folderName\ --region eu-west-1"
    
    Write-Host "Syncing $folderName..."
    Invoke-Expression $command
}