"""
MASTER DATA COLLECTION SCRIPT
Coordinates all scrapers to collect MAXIMUM politicians, elections, and officials

TARGET: 20,000-30,000+ total records
- Election Politicians (historical): 15,000-20,000
- Current Officials: 4,000-5,000  
- Election Schedules: 1,000+
"""

import sys
from pathlib import Path
import subprocess
from datetime import datetime

def run_command(cmd: list, description: str):
    """Run a command and display progress."""
    print("\n" + "="*80)
    print(f"🚀 {description}")
    print("="*80)
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        print(f"\n✅ {description} - COMPLETE")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} - FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ {description} - ERROR: {e}")
        return False


def main():
    """Master data collection orchestrator."""
    
    print("\n" + "="*80)
    print("🎯 MASTER DATA COLLECTION - MAXIMUM POLITICIANS & OFFICIALS")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nObjective: Collect 20,000-30,000+ total records")
    print("  • Election Politicians (10 years history): 15,000-20,000")
    print("  • Current Officials (National + Prefectural + Cities): 4,000-5,000")
    print("  • Election Schedules: 1,000+")
    print("="*80 + "\n")
    
    python = sys.executable
    results = {}
    
    # Phase 1: Scrape Election Politicians (HISTORICAL DATA - 2015-2025)
    # This will take 30-60 minutes but collect 15,000-20,000 politicians
    print("\n📍 PHASE 1/3: ELECTION POLITICIANS (Historical 2015-2025)")
    print("Expected: 15,000-20,000 politicians")
    print("Duration: ~30-60 minutes")
    print("-" * 80)
    
    cmd = [
        python,
        "scrape_elections.py",
        "--output", "data/outputs/politicians_from_elections_full.csv"
    ]
    results['elections'] = run_command(cmd, "Scrape Election Politicians (10 years)")
    
    # Phase 2: Scrape Current Officials (CURRENT DATA)
    # This will take 15-30 minutes and collect 4,000-5,000 current officials
    print("\n📍 PHASE 2/3: CURRENT OFFICIALS (National + Prefectural + Major Cities)")
    print("Expected: 4,000-5,000 current officials")
    print("Duration: ~15-30 minutes")
    print("-" * 80)
    
    cmd = [
        python,
        "scrape_current_officials.py",
        "--output", "data/outputs/current_officials.csv"
    ]
    results['officials'] = run_command(cmd, "Scrape Current Officials")
    
    # Phase 3: Clean All Data
    print("\n📍 PHASE 3/3: DATA CLEANING")
    print("Expected: Remove noise, standardize formats")
    print("Duration: ~1-2 minutes")
    print("-" * 80)
    
    cmd = [python, "clean_politician_data.py"]
    results['cleaning'] = run_command(cmd, "Clean Politician Data")
    
    # Summary
    print("\n" + "="*80)
    print("📊 MASTER COLLECTION SUMMARY")
    print("="*80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    for phase, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {phase.title()}: {status}")
    
    successful = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nOverall: {successful}/{total} phases completed")
    
    if successful == total:
        print("\n🎉 ALL PHASES COMPLETE!")
        print("\n📁 Output files:")
        print("  • data/outputs/politicians_from_elections_full.csv (15,000-20,000 records)")
        print("  • data/outputs/politicians_cleaned.csv (cleaned version)")
        print("  • data/outputs/current_officials.csv (4,000-5,000 records)")
        print("\n💡 Next steps:")
        print("  1. Review data quality in cleaned files")
        print("  2. Run: streamlit run app.py")
        print("  3. Verify all data displays correctly")
        print("  4. Commit and push to GitHub")
    else:
        print("\n⚠️  Some phases failed. Check logs above.")
    
    print("\n" + "="*80 + "\n")
    
    return successful == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
