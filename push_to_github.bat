@echo off
REM Quick script to push project to GitHub
REM Run this from project root directory

echo ========================================
echo   Pushing to GitHub Repository
echo ========================================
echo.

REM Check if git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed!
    echo Please install Git from: https://git-scm.com/downloads
    pause
    exit /b 1
)

echo Step 1: Initializing Git repository...
git init
if errorlevel 1 (
    echo ERROR: Failed to initialize git repository
    pause
    exit /b 1
)

echo.
echo Step 2: Adding all files...
git add .
if errorlevel 1 (
    echo ERROR: Failed to add files
    pause
    exit /b 1
)

echo.
echo Step 3: Creating initial commit...
git commit -m "Initial commit: Japanese Public Officials Data Collector v1.1.2"
if errorlevel 1 (
    echo Note: Files may already be committed
)

echo.
echo Step 4: Adding remote repository...
git remote add origin https://github.com/dalimoussa/-web-scraping-platform.git
if errorlevel 1 (
    echo Note: Remote may already exist
    git remote set-url origin https://github.com/dalimoussa/-web-scraping-platform.git
)

echo.
echo Step 5: Pushing to GitHub...
echo You may be prompted for GitHub credentials...
echo.
git branch -M main
git push -u origin main

if errorlevel 1 (
    echo.
    echo ========================================
    echo   Push Failed!
    echo ========================================
    echo.
    echo Possible solutions:
    echo 1. Check if repository exists at: https://github.com/dalimoussa/-web-scraping-platform
    echo 2. Verify you have write permissions
    echo 3. Use GitHub personal access token instead of password
    echo    Generate at: https://github.com/settings/tokens
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   SUCCESS! Project pushed to GitHub
echo ========================================
echo.
echo View your repository at:
echo https://github.com/dalimoussa/-web-scraping-platform
echo.
pause
