"""
Continue Municipal Scraping - Expand election schedule data
Scrapes remaining municipalities to get more scheduled elections
"""

import sys
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any
import time
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.scrapers.smart_municipal import SmartMunicipalScraper
from src.core.csv_exporter import CSVExporter


def scrape_municipalities(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Scrape municipalities to get scheduled elections.
    
    Args:
        limit: Number of municipalities to scrape
        
    Returns:
        List of officials/elections found
    """
    
    print("\n" + "="*80)
    print("🗺️ MUNICIPAL SCRAPER - Collecting Scheduled Elections")
    print(f"   Target: {limit} municipalities")
    print("   Fast scraping with 0.5s delay")
    print("="*80 + "\n")
    
    # Load municipal URLs
    urls_file = "data/outputs/municipal_urls.csv"
    if not Path(urls_file).exists():
        print(f"❌ Error: {urls_file} not found")
        return []
    
    urls_df = pd.read_csv(urls_file, encoding='utf-8-sig')
    print(f"📂 Loaded {len(urls_df)} municipal URLs\n")
    
    # Initialize scraper with HTTPClient
    from src.core.http_client import HTTPClient
    http_client = HTTPClient(
        default_delay=0.5,
        use_cache=True,
        max_retries=3,
        timeout=30
    )
    scraper = SmartMunicipalScraper(http_client=http_client)
    
    all_results = []
    start_time = time.time()
    
    # Take the first 'limit' municipalities
    urls_to_scrape = urls_df.head(limit)
    
    for idx, row in urls_to_scrape.iterrows():
        municipality = row.get('municipality', 'Unknown')
        url = row.get('url', '')
        
        if not url:
            continue
        
        print(f"[{idx+1}/{limit}] 🏛️  {municipality}")
        
        try:
            results = scraper.scrape(url)
            
            if results:
                # Add municipality info
                for result in results:
                    result['municipality'] = municipality
                    result['scraped_url'] = url
                    result['scraped_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                all_results.extend(results)
                print(f"  ✅ Found {len(results)} officials/elections")
            else:
                print(f"  ⚠️  No data found")
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue
        
        # Progress update every 10
        if (idx + 1) % 10 == 0:
            elapsed = time.time() - start_time
            rate = (idx + 1) / (elapsed / 60)
            print(f"\n  📊 Progress: {idx+1}/{limit} ({(idx+1)/limit*100:.1f}%)")
            print(f"  ⏱️  Speed: {rate:.1f} municipalities/minute")
            print(f"  ✅ Total collected: {len(all_results)} records\n")
    
    # Final stats
    elapsed = time.time() - start_time
    print(f"\n{'='*80}")
    print("📊 SCRAPING COMPLETE")
    print(f"{'='*80}")
    print(f"Total municipalities scraped: {limit}")
    print(f"Total officials/elections found: {len(all_results)}")
    print(f"Time elapsed: {elapsed/60:.1f} minutes")
    print(f"Average: {len(all_results)/limit:.1f} records per municipality")
    print(f"{'='*80}\n")
    
    return all_results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Continue municipal scraping")
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=100,
        help='Number of municipalities to scrape (default: 100)'
    )
    parser.add_argument(
        '--output', '-o',
        default='municipal_scraping_continued.csv',
        help='Output CSV filename'
    )
    
    args = parser.parse_args()
    
    # Extract just filename
    output_filename = Path(args.output).name
    
    try:
        print(f"\n🚀 Starting scraper for {args.limit} municipalities...")
        print(f"📁 Output will be saved to: data/outputs/{output_filename}\n")
        
        results = scrape_municipalities(limit=args.limit)
        
        if results:
            # Save results
            exporter = CSVExporter("data/outputs")
            exporter.export(results, output_filename)
            
            print(f"\n✅ Success! Collected {len(results)} records")
            print(f"📁 Saved to: data/outputs/{output_filename}")
            
            # Also merge with existing results
            existing_file = "data/outputs/municipal_scraping_results.csv"
            if Path(existing_file).exists():
                existing_df = pd.read_csv(existing_file, encoding='utf-8-sig')
                new_df = pd.read_csv(f"data/outputs/{output_filename}", encoding='utf-8-sig')
                
                # Combine
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df.to_csv(existing_file, index=False, encoding='utf-8-sig')
                
                print(f"✅ Merged with existing data: {len(combined_df)} total records")
                print(f"📁 Updated: {existing_file}\n")
        else:
            print("\n⚠️  No data collected. Check URLs or try different municipalities.\n")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
