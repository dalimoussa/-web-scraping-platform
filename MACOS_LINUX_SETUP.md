# macOS/Linux Setup Instructions

## 🍎 For macOS Users

### Step 1: Clone the Repository

```bash
# Open Terminal (Cmd + Space, type "Terminal")

# Clone the repository
git clone https://github.com/dalimoussa/-web-scraping-platform.git

# Navigate into the project
cd -web-scraping-platform
```

### Step 2: Make Scripts Executable

```bash
# Make all shell scripts executable
chmod +x setup.sh start_ui.sh push_to_github.sh
```

### Step 3: Run Setup

```bash
# Run the setup script
./setup.sh
```

This will:
- Create Python virtual environment
- Install all dependencies
- Verify installation

**Expected output:**
```
Creating Python virtual environment...
Installing dependencies...
✓ Setup complete!
```

### Step 4: Launch the UI

```bash
# Start the web interface
./start_ui.sh
```

**Expected output:**
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

### Step 5: Open in Browser

The browser should open automatically to: **http://localhost:8501**

If not, manually open that URL in your browser.

---

## 🐧 For Linux Users

Same instructions as macOS above!

---

## ❓ Common Issues

### Issue 1: "setup.sh: No such file or directory"

**Cause:** You're not in the project directory

**Solution:**
```bash
# Find where you cloned the repo
cd -web-scraping-platform

# Or if you downloaded it
cd ~/Downloads/-web-scraping-platform

# Verify you're in the right place
ls -la
# You should see: setup.sh, start_ui.sh, app.py, main.py, etc.
```

### Issue 2: "Permission denied"

**Cause:** Scripts are not executable

**Solution:**
```bash
chmod +x *.sh
```

### Issue 3: "Python not found" or "python3: command not found"

**Cause:** Python 3.10+ not installed

**Solution:**

**macOS:**
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3
brew install python@3.11
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

**Linux (CentOS/RHEL):**
```bash
sudo yum install python3.11
```

### Issue 4: "Port 8501 is already in use"

**Solution:**
```bash
# Find and kill the process
lsof -ti:8501 | xargs kill -9

# Or use a different port
streamlit run app.py --server.port 8502
```

---

## 🔍 Verify Installation

After setup, verify everything works:

```bash
# Activate virtual environment
source .venv/bin/activate

# Check Python version
python --version
# Should show: Python 3.10+ or higher

# Check installed packages
pip list | grep streamlit
# Should show: streamlit 1.28.0 or higher

# Test the CLI
python main.py version
# Should show: Version 1.1.2

# Deactivate when done
deactivate
```

---

## 🚀 Quick Reference

### Daily Use

```bash
# Navigate to project
cd -web-scraping-platform

# Launch UI
./start_ui.sh

# Stop UI
# Press Ctrl + C in the terminal
```

### Command Line Usage

```bash
# Activate environment
source .venv/bin/activate

# Run commands
python main.py scrape-officials --limit 10
python main.py scrape-elections --limit 20
python main.py run-all
python main.py clear-cache

# Deactivate
deactivate
```

---

## 📁 Project Structure (Verify You're in Right Place)

When you run `ls -la`, you should see:

```
-rw-r--r--  app.py
-rw-r--r--  main.py
-rwxr-xr-x  setup.sh           ← Should have 'x' (executable)
-rwxr-xr-x  start_ui.sh        ← Should have 'x' (executable)
drwxr-xr-x  src/
drwxr-xr-x  config/
drwxr-xr-x  data/
-rw-r--r--  README.md
-rw-r--r--  requirements.txt
```

---

## 💡 Pro Tips

### Tip 1: Use Tab Completion
```bash
# Type first few letters, then press Tab
cd -web<Tab>  # Auto-completes to -web-scraping-platform
./sta<Tab>    # Auto-completes to ./start_ui.sh
```

### Tip 2: Create Desktop Shortcut

**macOS:**
```bash
# Create an app launcher
cat > ~/Desktop/Launch-Scraper.command << 'EOF'
#!/bin/bash
cd ~/Downloads/-web-scraping-platform
./start_ui.sh
EOF

chmod +x ~/Desktop/Launch-Scraper.command
```

**Linux:**
```bash
# Create desktop entry
cat > ~/.local/share/applications/scraper.desktop << EOF
[Desktop Entry]
Name=Japanese Scraper
Exec=/path/to/-web-scraping-platform/start_ui.sh
Terminal=true
Type=Application
EOF
```

### Tip 3: Update Project

```bash
# Pull latest changes
git pull origin main

# Reinstall dependencies (if updated)
./setup.sh
```

---

## 🆘 Still Having Issues?

### Check System Requirements

```bash
# Check Python version
python3 --version

# Check if pip is installed
python3 -m pip --version

# Check if git is installed
git --version

# Check available disk space
df -h .
```

### View Logs

```bash
# Application logs
cat logs/scraper.log

# Or tail logs in real-time
tail -f logs/scraper.log
```

### Clean Install

```bash
# Remove virtual environment
rm -rf .venv

# Remove cache
rm -rf data/cache/*

# Run setup again
./setup.sh
```

---

## 📞 Contact

If you continue to have issues:

1. **Check README.md** - Main documentation
2. **Check QUICK_START.md** - Step-by-step guide
3. **Check logs** - `logs/scraper.log`
4. **GitHub Issues** - Report bugs at repository

---

## ✅ Expected First-Time Setup

Complete setup should take **3-5 minutes**:

1. Clone repo: **30 seconds**
2. Make executable: **5 seconds**
3. Run setup: **2-3 minutes** (downloads dependencies)
4. Launch UI: **10 seconds**
5. **DONE!** ✨

---

**Quick Start:**
```bash
git clone https://github.com/dalimoussa/-web-scraping-platform.git
cd -web-scraping-platform
chmod +x *.sh
./setup.sh
./start_ui.sh
```

Then open: **http://localhost:8501**

---

*For Windows users, see README.md or QUICK_START.md*
