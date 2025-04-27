#!/bin/bash
# Script to generate a complete .env.prod file with all required variables

# Check if .env.prod already exists
if [ -f ".env.prod" ]; then
  echo "File .env.prod already exists. Do you want to overwrite it? (y/n)"
  read answer
  if [ "$answer" != "y" ]; then
    echo "Aborting."
    exit 1
  fi
  # Make a backup copy
  cp .env.prod .env.prod.bak
  echo "Created backup at .env.prod.bak"
fi

# Copy example file as a starting point
cp .env.example .env.prod

# Add missing environment variables
echo "\n# Making sure all required variables are present" >> .env.prod
echo "APIFY_API_TOKEN=your_apify_token_here" >> .env.prod
echo "PHANTOMBUSTER_API_KEY=your_phantombuster_key_here" >> .env.prod
echo "CRAWL4AI_API_KEY=your_crawl4ai_key_here" >> .env.prod

echo ".env.prod file has been created with all required variables."
echo "IMPORTANT: Make sure to replace the placeholder values with your actual API keys."
