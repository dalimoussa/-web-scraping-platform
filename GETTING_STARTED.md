# 🚀 Getting Started - View Election Data Results

After cloning this repository, follow these simple steps to view the 7,336 politicians data in the web dashboard.

## 📋 Prerequisites

- Python 3.10 or higher
- Git (already installed if you cloned the repo)

## 🔧 Quick Setup (3 steps)

### Step 1: Clone the Repository
```bash
git clone https://github.com/dalimoussa/-web-scraping-platform.git
cd -web-scraping-platform
```

### Step 2: Install Dependencies
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### Step 3: Launch the Dashboard
```bash
streamlit run app.py
```

That's it! The dashboard will automatically open in your browser at **http://localhost:8501**

## 📊 What You'll See

The dashboard includes:

### **🏛️ Election Politicians Tab** (Main Feature)
- **7,336 politicians** from all 47 Japanese prefectures
- **Filters**: 
  - Prefecture selector
  - Political party filter
  - Name search
  - Election year filter
- **Statistics**:
  - Top 10 prefectures by politician count
  - Top 10 political parties
- **Download**: Export filtered data as CSV

### **📈 Dashboard Overview**
- Total politicians count: 7,336
- 100% prefecture coverage (47/47)
- 100% with election dates
- Quality score: 95.4%

### **Other Tabs**:
- Officials (original 2 officials from v1.1.2)
- Elections (226 scheduled elections)
- Municipal Scraping (1,747 municipalities)
- Funding data
- Files (download all datasets)

## 📁 Key Data Files

All data is in the `data/outputs/` folder:

- **`politicians_cleaned.csv`** - ⭐ **Main deliverable**: 7,336 cleaned politicians
- **`politicians_from_elections.csv`** - Raw data (7,693 records before cleaning)
- `officials.csv` - Original 2 officials
- `elections.csv` - 226 election schedules
- `municipal_urls.csv` - 1,747 municipal URLs

## 🔍 Browse the Data

### Option 1: Web Dashboard (Recommended)
```bash
streamlit run app.py
```
- Interactive filters
- Visual charts
- Easy downloads

### Option 2: Direct CSV Access
```bash
# Open in Excel/LibreOffice
data/outputs/politicians_cleaned.csv

# Or view in terminal
head -20 data/outputs/politicians_cleaned.csv
```

### Option 3: Python Script
```python
import pandas as pd

# Load the data
df = pd.read_csv('data/outputs/politicians_cleaned.csv', encoding='utf-8-sig')

print(f"Total politicians: {len(df)}")
print(f"\nPrefectures: {df['prefecture'].nunique()}")
print(f"\nTop 5 prefectures:")
print(df['prefecture'].value_counts().head())
```

## 📊 Data Schema

Each politician record includes:

| Field | Description | Example |
|-------|-------------|---------|
| `name` | Politician's name | 山田太郎 |
| `prefecture` | Prefecture | 東京都 |
| `election` | Election name | 東京都議会議員選挙（2021年7月4日投票）結果 |
| `election_date` | Election date (YYYY-MM-DD) | 2021-07-04 |
| `source` | Data source | seijiyama.jp/elections |
| `source_url` | Source URL | https://seijiyama.jp/... |
| `scraped_at` | Collection timestamp | 2025-10-28 11:54:06 |

## 🎯 Quick Stats

- **Total Politicians**: 7,336
- **Prefectures Covered**: 47/47 (100%)
- **Data Quality**: 95.4%
- **Elections Scraped**: 940
- **Collection Method**: Public election results (seijiyama.jp)
- **Collection Date**: October 28, 2025

## 🛠️ Advanced Usage

### Re-run Data Collection
```bash
# Scrape elections again (takes ~1 hour)
python scrape_elections.py --limit-per-prefecture 20 --delay 2.0

# Clean the data
python clean_politician_data.py
```

### Filter Data in Python
```python
import pandas as pd

df = pd.read_csv('data/outputs/politicians_cleaned.csv', encoding='utf-8-sig')

# Filter by prefecture
tokyo = df[df['prefecture'] == '東京都']
print(f"Tokyo politicians: {len(tokyo)}")

# Filter by election year
df['year'] = pd.to_datetime(df['election_date']).dt.year
recent = df[df['year'] >= 2020]
print(f"Recent elections (2020+): {len(recent)}")
```

## 🐛 Troubleshooting

### Dashboard won't start
```bash
# Make sure you're in the virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux

# Reinstall streamlit
pip install streamlit --upgrade
```

### CSV encoding issues in Excel
- Use UTF-8-sig encoding
- Or import using "Text Import Wizard" and select UTF-8

### Missing data files
```bash
# Check if files exist
ls data/outputs/politicians_cleaned.csv

# If missing, download from release or re-run scraper
python scrape_elections.py --limit-per-prefecture 20
python clean_politician_data.py
```

## 📞 Support

If you encounter issues:
1. Check that all files are in `data/outputs/`
2. Verify Python version: `python --version` (should be 3.10+)
3. Check the TODO list in the repository
4. Review commit history for recent changes

## 🎉 You're All Set!

The dashboard should be running at **http://localhost:8501**

Navigate to the **"🏛️ Election Politicians"** tab to see the main dataset.

Happy exploring! 🚀
