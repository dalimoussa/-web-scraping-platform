# 🚀 Quick Start Guide

**Get started with the Japanese Public Officials Data Collector in 5 minutes!**

---

## 📋 Before You Begin

Make sure you have:
- ✅ Python 3.10 or newer installed
- ✅ Internet connection
- ✅ Modern web browser (Chrome, Firefox, Edge)

---

## Step 1: Download & Setup (2 minutes)

### Windows Users:

1. **Open PowerShell** in the project folder
2. **Run the setup script**:
   ```powershell
   .\setup.ps1
   ```
3. **Wait** for dependencies to install (this happens once)

### macOS/Linux Users:

1. **Open Terminal** in the project folder
2. **Make script executable and run**:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
3. **Wait** for dependencies to install (this happens once)

**✅ Setup complete!** You should see a success message.

---

## Step 2: Launch the Web Interface (30 seconds)

### Windows:
**Double-click** `start_ui.bat` file

OR run in PowerShell:
```powershell
.\start_ui.bat
```

### macOS/Linux:
Run in Terminal:
```bash
./start_ui.sh
```

**What you'll see:**
- Terminal window opens
- "You can now view your Streamlit app..." message
- Local URL appears: `http://localhost:8501`

**⚠️ Don't close the terminal window!** Keep it running.

---

## Step 3: Open the Dashboard (10 seconds)

1. **Open your web browser**
2. **Go to**: `http://localhost:8501`
3. **Bookmark it** for easy access

**🎉 Success!** You should see the dashboard.

---

## Step 4: Collect Your First Data (1 minute)

### In the Web Interface:

1. **Look at the left sidebar**
2. **Uncheck "Limit results"** (or keep it for testing)
3. **Click one of the scraper buttons**:
   - 🏛️ **Officials** - Public officials data
   - 🗳️ **Elections** - Election information
   - 💰 **Funding** - Political funding
   - 🚀 **Run All** - Collect everything

4. **Watch the progress** (shows live updates)
5. **See the results** in the success message

### View Your Data:

1. **Click the tab** at the top:
   - **Dashboard** - Overview
   - **Officials** - Officials data
   - **Elections** - Election data
   - **Funding** - Funding data
   - **Files** - All CSV files

2. **Use the filters** to search and sort
3. **Click 📥 Download** to save as CSV

---

## Step 5: Export to Excel (30 seconds)

Your data is automatically saved to:
```
data/outputs/
├── officials.csv
├── officials_sns.csv
├── elections.csv
├── election_results.csv
└── funding.csv
```

**To open in Excel:**
1. Navigate to `data/outputs/` folder
2. Double-click any CSV file
3. Excel opens with perfect Japanese characters!

---

## 🎯 Common Tasks

### Task: Clear Cache (if you see garbled text)
1. In the sidebar, click **"Clear Cache"**
2. Re-run your scraper
3. Data will be fresh with correct encoding

### Task: Run from Command Line
```bash
# Activate environment
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate # macOS/Linux

# Run commands
python main.py scrape-officials --limit 5
python main.py scrape-elections --limit 10
python main.py run-all
```

### Task: Stop the Server
- **Close the terminal window**, or
- **Press `Ctrl + C`** in the terminal

### Task: Restart the Server
- **Run** `start_ui.bat` (Windows) or `./start_ui.sh` (macOS/Linux) again

---

## ❓ Troubleshooting

### Problem: "Module not found" error
**Solution:**
```bash
# Activate environment first
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Problem: Port 8501 already in use
**Solution:**
- Close other Streamlit apps
- Or change port: `streamlit run app.py --server.port 8502`

### Problem: Browser doesn't open automatically
**Solution:**
- Manually open: `http://localhost:8501`
- Check terminal for the correct URL

### Problem: No data appears
**Solution:**
1. Check internet connection
2. Look in sidebar for error messages
3. Check `logs/scraper.log` for details

### Problem: Garbled Japanese characters
**Solution:**
1. Click **"Clear Cache"** in sidebar
2. Re-scrape the data
3. Encoding will be fixed automatically

---

## 📚 Next Steps

- **Explore the Dashboard** - See all available data
- **Try Filters** - Search by name, date, jurisdiction
- **Export Data** - Download CSV files for analysis
- **Read README.md** - Learn advanced features
- **Check CHANGELOG.md** - See what's new

---

## 💡 Pro Tips

- **Bookmark** `http://localhost:8501` in your browser
- **Keep terminal open** while using the UI
- **Check logs** in `logs/scraper.log` for detailed information
- **Use filters** to find exactly what you need
- **Download CSV** for offline analysis in Excel

---

## 🆘 Still Need Help?

1. **Check** `logs/scraper.log` for error messages
2. **Verify** Python version: `python --version` (should be 3.10+)
3. **Review** troubleshooting section above
4. **Re-run** setup script if installations failed

---

## ✅ Checklist

Before starting, make sure:
- [ ] Python 3.10+ installed
- [ ] Setup script completed successfully
- [ ] Terminal stays open when running UI
- [ ] Browser can access localhost:8501
- [ ] Internet connection is active

---

**You're all set! Happy data collecting!** 🎉

---

*Need more details? Check out README.md for comprehensive documentation.*
