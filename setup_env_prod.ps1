# PowerShell script to generate a complete .env.prod file with all required variables

# Check if .env.prod already exists
if (Test-Path ".env.prod") {
    $answer = Read-Host "File .env.prod already exists. Do you want to overwrite it? (y/n)"
    if ($answer -ne "y") {
        Write-Host "Aborting."
        exit 1
    }
    # Make a backup copy
    Copy-Item -Path ".env.prod" -Destination ".env.prod.bak"
    Write-Host "Created backup at .env.prod.bak"
}

# Copy example file as a starting point
Copy-Item -Path ".env.example" -Destination ".env.prod"

# Add missing environment variables
Add-Content -Path ".env.prod" -Value "
# Making sure all required variables are present"
Add-Content -Path ".env.prod" -Value "APIFY_API_TOKEN=your_apify_token_here"
Add-Content -Path ".env.prod" -Value "PHANTOMBUSTER_API_KEY=your_phantombuster_key_here"
Add-Content -Path ".env.prod" -Value "CRAWL4AI_API_KEY=your_crawl4ai_key_here"

Write-Host ".env.prod file has been created with all required variables."
Write-Host "IMPORTANT: Make sure to replace the placeholder values with your actual API keys."
