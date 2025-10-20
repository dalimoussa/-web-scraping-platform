# 🎉 Release v1.1.2 - Japanese Public Officials Data Collector

**Release Date**: October 20, 2025  
**Status**: Production Ready  
**Type**: Patch Release (Encoding Fix)

---

## 📦 What's Included

This is a complete, production-ready web scraping platform with:

- ✅ **Web Dashboard** - Beautiful Streamlit UI
- ✅ **Command Line Interface** - For automation
- ✅ **3 Data Scrapers** - Officials, Elections, Funding
- ✅ **CSV Export** - Excel-compatible output
- ✅ **Japanese Encoding** - Perfect UTF-8 and Shift_JIS support
- ✅ **Caching System** - Fast repeat queries
- ✅ **Rate Limiting** - Respectful scraping
- ✅ **Error Handling** - Robust and reliable

---

## 🆕 What's New in v1.1.2

### 🔧 Bug Fixes
- **Fixed Japanese character encoding** - Garbled text (e.g., "CRecÕWv") now displays correctly
- **Added Shift_JIS auto-detection** - Handles Japanese government websites properly
- **Fixed Streamlit deprecation warnings** - Updated to latest API

### ✨ New Features
- **Clear Cache Command** - `python main.py clear-cache` or UI button
- **Enhanced Error Messages** - Better troubleshooting information
- **Improved Logging** - More detailed debug information

### 📚 Documentation
- **Simplified README** - Focus on getting started quickly
- **New QUICK_START Guide** - Step-by-step tutorial
- **Cleaned up project** - Removed redundant technical docs

---

## 🚀 Installation

### Requirements
- Python 3.10 or higher
- Internet connection
- 100MB free disk space

### Quick Install

**Windows:**
```powershell
.\setup.ps1
```

**macOS/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

This will:
1. Create a Python virtual environment
2. Install all dependencies
3. Verify the installation
4. Ready to use!

---

## 🎯 Quick Start

### Launch Web UI (Recommended)

**Windows:**
```powershell
.\start_ui.bat
```

**macOS/Linux:**
```bash
./start_ui.sh
```

Then open: **http://localhost:8501**

### Command Line Usage

```bash
# Activate environment first
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate # macOS/Linux

# Collect data
python main.py scrape-officials --limit 10
python main.py scrape-elections --limit 20
python main.py scrape-funding --limit 5
python main.py run-all

# Utility commands
python main.py clear-cache
python main.py version
python main.py info
```

---

## 📊 Features Overview

### Web Dashboard
- **Real-time Statistics** - See data counts at a glance
- **Interactive Tables** - Search, filter, sort data
- **Live Scraping** - Watch progress in real-time
- **One-click Export** - Download CSV files instantly
- **Cache Management** - Clear button for fresh data

### Data Collection
- **Public Officials** - Names, ages, factions, SNS profiles
- **Election Data** - Schedules, results, jurisdictions
- **Political Funding** - Financial disclosure information

### Technical Features
- **Rate Limiting** - Configurable delays between requests
- **HTTP Caching** - Speeds up repeat queries
- **Robots.txt Compliance** - Respects website policies
- **Automatic Retries** - Handles network errors gracefully
- **UTF-8 BOM Export** - Perfect Excel compatibility

---

## 📁 Project Structure

```
discord project/
├── README.md              # Main documentation
├── QUICK_START.md         # Beginner's guide
├── CHANGELOG.md           # Version history
├── RELEASE_NOTES.md       # This file
├── requirements.txt       # Python dependencies
│
├── app.py                 # Web UI (Streamlit)
├── main.py                # CLI interface
├── start_ui.bat           # Windows launcher
├── start_ui.sh            # macOS/Linux launcher
├── setup.ps1              # Windows setup
├── setup.sh               # macOS/Linux setup
│
├── src/                   # Source code
│   ├── scrapers/          # Data collection
│   ├── core/              # Core utilities
│   ├── utils/             # Helper functions
│   └── models/            # Data schemas
│
├── config/                # Configuration
│   ├── config.yaml        # Main settings
│   └── sources.yaml       # Data sources
│
├── data/                  # Data storage
│   ├── outputs/           # CSV files (your data!)
│   ├── cache/             # HTTP cache
│   └── state/             # Application state
│
├── logs/                  # Application logs
└── tests/                 # Unit tests
```

---

## 📥 Output Files

All data saved to `data/outputs/`:

| File | Description | Encoding |
|------|-------------|----------|
| `officials.csv` | Public officials data | UTF-8 BOM |
| `officials_sns.csv` | Social media profiles | UTF-8 BOM |
| `elections.csv` | Election schedules | UTF-8 BOM |
| `election_results.csv` | Election outcomes | UTF-8 BOM |
| `funding.csv` | Political funding | UTF-8 BOM |

**UTF-8 BOM** = Opens perfectly in Excel with Japanese characters

---

## ⚙️ Configuration

### Main Settings (`config/config.yaml`)

```yaml
scraping:
  default_delay: 1.5        # Seconds between requests
  max_retries: 3            # Retry attempts
  timeout: 30               # Request timeout
  use_cache: true           # Enable HTTP caching
  respect_robots_txt: true  # Follow robots.txt

output:
  directory: "data/outputs"
  encoding: "utf-8-sig"     # Excel-compatible

logging:
  level: "INFO"
  file: "logs/scraper.log"
  console_output: true
```

### Data Sources (`config/sources.yaml`)

Add or modify URLs for scraping:

```yaml
officials:
  - name: "Example Official"
    url: "https://example.com"
    
elections:
  - name: "SOUMU Election Committee"
    url: "https://www.soumu.go.jp/senkyo/..."
```

---

## 🔧 Troubleshooting

### Encoding Issues (Garbled Japanese)
1. Click **"Clear Cache"** in web UI
2. Re-scrape the data
3. Encoding fix applies automatically

### Installation Problems
```bash
# Verify Python version
python --version  # Should be 3.10+

# Reinstall dependencies
pip install -r requirements.txt

# Check logs
cat logs/scraper.log  # macOS/Linux
type logs\scraper.log  # Windows
```

### UI Won't Start
```bash
# Try running directly
streamlit run app.py

# Check if port is in use
netstat -an | findstr "8501"  # Windows
lsof -i :8501                 # macOS/Linux
```

### No Data Collected
- Verify internet connection
- Check `logs/scraper.log` for errors
- Ensure URLs in `config/sources.yaml` are valid
- Try with `--verbose` flag for debug info

---

## 📈 Version History

### v1.1.2 (2025-10-20) - Current
- Fixed Japanese character encoding (Shift_JIS support)
- Added clear cache functionality
- Updated documentation

### v1.1.1 (2025-10-17)
- Fixed ElectionsScraper abstract method bug
- All integration tests passing

### v1.1.0 (2025-10-17)
- Added Streamlit web interface
- Advanced features (JS rendering, PDF parsing)
- Comprehensive testing suite

### v1.0.0 (2025-10-15)
- Initial release
- CLI interface
- Core scraping functionality

---

## 🎯 Use Cases

- **Academic Research** - Study Japanese political trends
- **Journalism** - Access public official information
- **Data Analysis** - Analyze election results
- **Civic Monitoring** - Track political funding
- **Automation** - Schedule regular data collection

---

## 📝 Dependencies

### Core
- Python 3.10+
- requests 2.31.0
- beautifulsoup4 4.12.0
- pandas 2.1.0
- streamlit 1.28.0

### Utilities
- typer 0.9.0 (CLI)
- rich 13.6.0 (Terminal output)
- pydantic 2.4.0 (Data validation)
- pyyaml 6.0.1 (Configuration)

See `requirements.txt` for complete list.

---

## 🔒 Privacy & Ethics

This tool:
- ✅ Only collects **publicly available** information
- ✅ Respects **robots.txt** rules
- ✅ Implements **rate limiting**
- ✅ Caches responses to **minimize requests**
- ✅ Follows **best practices** for web scraping

**Use responsibly!**

---

## 📄 License

MIT License - Free for research, educational, and commercial use.

---

## 🤝 Support

### Documentation
- **README.md** - Main documentation
- **QUICK_START.md** - Step-by-step tutorial
- **CHANGELOG.md** - Detailed version history

### Getting Help
1. Check troubleshooting section above
2. Review `logs/scraper.log`
3. Verify configuration in `config/`
4. Check GitHub issues (if applicable)

---

## ✅ Quality Assurance

This release has been tested with:
- ✅ 13/13 unit tests passing
- ✅ All CLI commands working
- ✅ Web UI fully functional
- ✅ Data export verified
- ✅ Encoding fix confirmed
- ✅ Documentation reviewed

---

## 🚀 Next Steps

1. **Run** `setup.ps1` (Windows) or `setup.sh` (macOS/Linux)
2. **Launch** UI with `start_ui.bat` or `start_ui.sh`
3. **Open** http://localhost:8501
4. **Click** scraper buttons to collect data
5. **Explore** and download your data!

---

## 📧 Contact

For questions or issues:
- Check documentation first
- Review logs in `logs/scraper.log`
- Verify configuration settings

---

**Thank you for using Japanese Public Officials Data Collector!**

*This is a production-ready release. All systems operational.* ✅

---

*Last updated: October 20, 2025 | Version 1.1.2*
