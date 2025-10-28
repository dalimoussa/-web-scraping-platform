# 🏛️ Japanese Public Officials Data Collector

> **Professional web scraping platform for Japanese political data with a beautiful web interface**

![Version 1.1.2](https://img.shields.io/badge/version-1.1.2-blue) ![Python 3.10+](https://img.shields.io/badge/python-3.10+-green) ![Status: Ready](https://img.shields.io/badge/status-ready-success)

## 🎯 **NEW: Milestone 1 Complete!**
✅ **7,336 politicians** collected from all 47 Japanese prefectures  
✅ **95.4% data quality** with comprehensive filtering  
✅ **Interactive dashboard** with search and export features  

👉 **[Quick Start Guide →](GETTING_STARTED.md)** - View the data in 3 steps!

---

## ✨ What This Does

Automatically collects and organizes Japanese political data:
- **🏛️ Election Politicians**: 7,336 politicians from all 47 prefectures (NEW!)
- **👤 Public Officials**: Names, ages, factions, SNS profiles
- **🗳️ Elections**: Schedules, results, jurisdictions
- **💰 Funding**: Political finance information
- **📊 Web Dashboard**: Interactive UI for exploring data
- **📥 Export**: Excel-compatible CSV files

---

## 🚀 Quick Start (30 seconds)

### Step 1: Install
```bash
# Windows
.\setup.ps1

# macOS/Linux
chmod +x setup.sh && ./setup.sh
```

### Step 2: Launch UI
```bash
# Windows
.\start_ui.bat

# macOS/Linux
./start_ui.sh
```

### Step 3: Open Browser
Go to: **http://localhost:8501**

**That's it!** 🎉

---

## 🖥️ Using the Web Interface

### Dashboard
- View real-time statistics
- See recent data previews
- Monitor scraping progress

### Collecting Data
1. **Open sidebar** (left side)
2. **Click scraper button**:
   - 🏛️ Officials
   - 🗳️ Elections
   - 💰 Funding
   - 🚀 Run All
3. **Wait for completion** (progress shown live)
4. **View results** in the data tabs

### Finding Data
- **Search**: Type names or keywords
- **Filter**: Select jurisdictions, factions, dates
- **Download**: Click 📥 button for CSV export

### If You See Garbled Text
1. Click **"Clear Cache"** in sidebar
2. Re-run the scraper
3. Japanese characters will display correctly

---

## 💻 Command Line (Optional)

For automation or advanced usage:

```bash
# Activate environment first
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate # macOS/Linux

# Collect data
python main.py scrape-officials --limit 10
python main.py scrape-elections --limit 20
python main.py run-all

# Utility commands
python main.py clear-cache
python main.py version
python main.py info
```

---

## 📁 Where's My Data?

All files saved to `data/outputs/`:

| File | Content |
|------|---------|
| `officials.csv` | Public officials data |
| `officials_sns.csv` | Social media profiles |
| `elections.csv` | Election schedules |
| `election_results.csv` | Election outcomes |
| `funding.csv` | Funding information |

**Format**: UTF-8 BOM (opens perfectly in Excel)

---

## ⚙️ Configuration

Edit `config/config.yaml` to customize:

```yaml
scraping:
  default_delay: 1.5    # Seconds between requests
  use_cache: true       # Cache HTTP responses
  
output:
  directory: "data/outputs"
  encoding: "utf-8-sig"  # Excel compatible
  
logging:
  level: "INFO"
  file: "logs/scraper.log"
```

Edit `config/sources.yaml` to add data sources.

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| **UI won't start** | Run `pip install -r requirements.txt` |
| **Garbled Japanese** | Click "Clear Cache" in UI, re-scrape |
| **No data collected** | Check internet connection and `logs/scraper.log` |
| **Port 8501 in use** | Close other Streamlit apps or change port |

**View detailed logs**: `logs/scraper.log`

---

## 📋 Requirements

- Python 3.10+
- Internet connection
- 100MB free disk space
- Modern web browser

---

## 📦 Project Structure

```
discord project/
├── app.py              # Web UI (launch this!)
├── main.py             # Command line interface
├── start_ui.bat        # Windows launcher
├── start_ui.sh         # macOS/Linux launcher
├── requirements.txt    # Dependencies
├── src/
│   ├── scrapers/       # Data collection logic
│   ├── core/           # HTTP client, config, CSV export
│   └── utils/          # Helper functions
├── config/             # Configuration files
├── data/
│   ├── outputs/        # Your CSV files here!
│   └── cache/          # HTTP cache
├── logs/               # Application logs
└── tests/              # Unit tests
```

---

## 📚 Documentation

- **QUICK_START.md** - Beginner's step-by-step guide
- **CHANGELOG.md** - Version history
- Inline code comments
- Help tooltips in web UI

---

## 🆕 Version 1.1.2 (Latest)

**What's New:**
- ✅ Fixed Japanese encoding (Shift_JIS support)
- ✅ Added "Clear Cache" button
- ✅ Improved error messages
- ✅ Updated all dependencies

**Previous Versions:**
- v1.1.1: Bug fixes for elections scraper
- v1.1.0: Web UI launch + advanced features
- v1.0.0: Initial CLI release

---

## 🎯 Use Cases

- **Research**: Analyze political trends and patterns
- **Journalism**: Access public official information
- **Data Analysis**: Study election results and funding
- **Monitoring**: Track changes over time

---

## 🤝 Support

**Need help?**
1. Check troubleshooting section above
2. Review `logs/scraper.log`
3. Verify Python version: `python --version`
4. Ensure all dependencies installed

---

## 📄 License

MIT License - Free for research and educational use

---

## 🎉 Ready to Start?

```bash
# Windows: Double-click this file
start_ui.bat

# macOS/Linux: Run in terminal
./start_ui.sh
```

Then open: **http://localhost:8501**

---

**Made with ❤️ for Japanese political data research**

*Last updated: October 20, 2025 | Version 1.1.2*
