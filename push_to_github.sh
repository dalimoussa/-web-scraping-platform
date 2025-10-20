#!/bin/bash
# Quick script to push project to GitHub
# Run this from project root directory

echo "========================================"
echo "  Pushing to GitHub Repository"
echo "========================================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "ERROR: Git is not installed!"
    echo "Please install Git from: https://git-scm.com/downloads"
    exit 1
fi

echo "Step 1: Initializing Git repository..."
git init
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to initialize git repository"
    exit 1
fi

echo ""
echo "Step 2: Adding all files..."
git add .
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to add files"
    exit 1
fi

echo ""
echo "Step 3: Creating initial commit..."
git commit -m "Initial commit: Japanese Public Officials Data Collector v1.1.2"
if [ $? -ne 0 ]; then
    echo "Note: Files may already be committed"
fi

echo ""
echo "Step 4: Adding remote repository..."
git remote add origin https://github.com/dalimoussa/-web-scraping-platform.git
if [ $? -ne 0 ]; then
    echo "Note: Remote may already exist"
    git remote set-url origin https://github.com/dalimoussa/-web-scraping-platform.git
fi

echo ""
echo "Step 5: Pushing to GitHub..."
echo "You may be prompted for GitHub credentials..."
echo ""
git branch -M main
git push -u origin main

if [ $? -ne 0 ]; then
    echo ""
    echo "========================================"
    echo "  Push Failed!"
    echo "========================================"
    echo ""
    echo "Possible solutions:"
    echo "1. Check if repository exists at: https://github.com/dalimoussa/-web-scraping-platform"
    echo "2. Verify you have write permissions"
    echo "3. Use GitHub personal access token instead of password"
    echo "   Generate at: https://github.com/settings/tokens"
    echo ""
    exit 1
fi

echo ""
echo "========================================"
echo "  SUCCESS! Project pushed to GitHub"
echo "========================================"
echo ""
echo "View your repository at:"
echo "https://github.com/dalimoussa/-web-scraping-platform"
echo ""
