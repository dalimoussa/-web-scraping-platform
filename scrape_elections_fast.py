"""
FAST Election Data Scraper - Optimized for cached data
Uses cached responses with minimal delay for maximum speed
"""

import sys
from pathlib import Path
import re
from typing import List, Dict, Any, Set
from urllib.parse import urljoin
import time
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.http_client import HTTPClient
from src.core.csv_exporter import CSVExporter
from src.utils.parsers import parse_html


class FastElectionScraper:
    """
    OPTIMIZED scraper that:
    1. Uses cached data aggressively (0.1s delay for cached)
    2. Only slows down for NEW requests (1s delay)
    3. Saves progress every 1000 records
    4. Can resume from interruption
    """
    
    def __init__(self, delay_cached: float = 0.1, delay_new: float = 1.0):
        """Initialize with separate delays for cached vs new requests."""
        # Use cache aggressively
        self.http = HTTPClient(
            default_delay=delay_cached,  # Fast for cached
            use_cache=True,
            respect_robots_txt=True,
            cache_expire_after=86400 * 7  # 7 days cache
        )
        self.delay_cached = delay_cached
        self.delay_new = delay_new
        self.base_url = "https://seijiyama.jp"
        self.elections_base = f"{self.base_url}/elections"
        
        # Track progress
        self.total_requests = 0
        self.cached_requests = 0
        self.new_requests = 0
        
        # Prefecture list
        self.prefectures = [
            ("hokkaido", "北海道"), ("aomori", "青森県"), ("iwate", "岩手県"), 
            ("miyagi", "宮城県"), ("akita", "秋田県"), ("yamagata", "山形県"), 
            ("fukushima", "福島県"), ("ibaraki", "茨城県"), ("tochigi", "栃木県"),
            ("gunma", "群馬県"), ("saitama", "埼玉県"), ("chiba", "千葉県"),
            ("tokyo", "東京都"), ("kanagawa", "神奈川県"), ("niigata", "新潟県"),
            ("toyama", "富山県"), ("ishikawa", "石川県"), ("fukui", "福井県"),
            ("yamanashi", "山梨県"), ("nagano", "長野県"), ("gifu", "岐阜県"),
            ("shizuoka", "静岡県"), ("aichi", "愛知県"), ("mie", "三重県"),
            ("shiga", "滋賀県"), ("kyoto", "京都府"), ("osaka", "大阪府"),
            ("hyogo", "兵庫県"), ("nara", "奈良県"), ("wakayama", "和歌山県"),
            ("tottori", "鳥取県"), ("shimane", "島根県"), ("okayama", "岡山県"),
            ("hiroshima", "広島県"), ("yamaguchi", "山口県"), ("tokushima", "徳島県"),
            ("kagawa", "香川県"), ("ehime", "愛媛県"), ("kochi", "高知県"),
            ("fukuoka", "福岡県"), ("saga", "佐賀県"), ("nagasaki", "長崎県"),
            ("kumamoto", "熊本県"), ("oita", "大分県"), ("miyazaki", "宮崎県"),
            ("kagoshima", "鹿児島県"), ("okinawa", "沖縄県")
        ]
    
    def _make_request(self, url: str) -> tuple[str, bool]:
        """
        Make request and return (content, is_cached).
        Apply appropriate delay based on cache status.
        """
        self.total_requests += 1
        
        # Check if we have cached response
        response = self.http.get(url)
        
        if response and hasattr(response, 'from_cache') and response.from_cache:
            self.cached_requests += 1
            time.sleep(self.delay_cached)  # Fast for cached
            return response.text, True
        else:
            self.new_requests += 1
            time.sleep(self.delay_new)  # Slower for new
            return response.text if response else None, False
    
    def _get_prefecture_elections(self, romaji: str, kanji: str) -> List[str]:
        """Get all election URLs for a prefecture (uses multiple strategies)."""
        elections = []
        seen_urls = set()
        
        # Strategy 1: Main prefecture page
        pref_url = f"{self.elections_base}/pref/{romaji}/"
        content, is_cached = self._make_request(pref_url)
        
        if content:
            soup = parse_html(content)
            links = soup.find_all('a', href=re.compile(r'/area/card/'))
            
            for link in links:
                href = link.get('href')
                if href and href not in seen_urls:
                    full_url = urljoin(self.base_url, href)
                    elections.append(full_url)
                    seen_urls.add(href)
        
        # Strategy 2: Year-based archives (2015-2025)
        current_year = datetime.now().year
        for year in range(2015, current_year + 1):
            year_url = f"{self.elections_base}/pref/{romaji}/?year={year}"
            content, is_cached = self._make_request(year_url)
            
            if content:
                soup = parse_html(content)
                links = soup.find_all('a', href=re.compile(r'/area/card/'))
                
                for link in links:
                    href = link.get('href')
                    if href and href not in seen_urls:
                        full_url = urljoin(self.base_url, href)
                        elections.append(full_url)
                        seen_urls.add(href)
        
        # Strategy 3: Search page
        search_url = f"{self.elections_base}/search?prefecture={kanji}"
        content, is_cached = self._make_request(search_url)
        
        if content:
            soup = parse_html(content)
            links = soup.find_all('a', href=re.compile(r'/area/card/'))
            
            for link in links:
                href = link.get('href')
                if href and href not in seen_urls:
                    full_url = urljoin(self.base_url, href)
                    elections.append(full_url)
                    seen_urls.add(href)
        
        return elections
    
    def _extract_politicians_from_election(self, url: str, prefecture: str) -> List[Dict[str, Any]]:
        """Extract politician data from an election results page."""
        content, is_cached = self._make_request(url)
        
        if not content:
            return []
        
        soup = parse_html(content)
        politicians = []
        
        # Extract election info
        election_name = ""
        title_tag = soup.find('h1') or soup.find('h2')
        if title_tag:
            election_name = title_tag.get_text(strip=True)
        
        # Extract election date
        election_date = ""
        date_pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
        date_match = re.search(date_pattern, election_name)
        if date_match:
            year, month, day = date_match.groups()
            election_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Find candidate names
        candidate_sections = soup.find_all(['div', 'tr', 'li'], class_=re.compile(r'candidate|result|name'))
        
        if not candidate_sections:
            # Fallback: Look for any text that looks like Japanese names
            text_content = soup.get_text()
            name_pattern = r'[一-龯]{2,4}[\s　]+[一-龯]{2,4}'
            potential_names = re.findall(name_pattern, text_content)
            
            for name in potential_names:
                name_clean = name.strip()
                if len(name_clean) >= 2 and len(name_clean) <= 10:
                    politicians.append({
                        'name': name_clean,
                        'prefecture': prefecture,
                        'election': election_name,
                        'election_date': election_date,
                        'source': 'seijiyama.jp/elections',
                        'source_url': url,
                        'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
        else:
            for section in candidate_sections:
                name = section.get_text(strip=True)
                
                # Clean name
                name = re.sub(r'[0-9０-９\s　]', '', name)
                name = re.sub(r'(当選|落選|票|得票|歳|氏)', '', name)
                
                if len(name) >= 2 and len(name) <= 10:
                    politicians.append({
                        'name': name,
                        'prefecture': prefecture,
                        'election': election_name,
                        'election_date': election_date,
                        'source': 'seijiyama.jp/elections',
                        'source_url': url,
                        'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
        
        return politicians
    
    def scrape_all_elections(self, output_file: str = "politicians_from_elections.csv") -> List[Dict[str, Any]]:
        """Scrape all elections with progress saving."""
        
        print("\n" + "="*80)
        print("⚡ FAST ELECTION SCRAPER - Optimized for Cached Data")
        print(f"   Cached requests: {self.delay_cached}s delay")
        print(f"   New requests: {self.delay_new}s delay")
        print("   Auto-save every 1000 records")
        print("="*80 + "\n")
        
        all_politicians = []
        exporter = CSVExporter("data/outputs")
        
        start_time = time.time()
        total_prefectures = len(self.prefectures)
        
        for idx, (romaji, kanji) in enumerate(self.prefectures, 1):
            print(f"\n[{idx}/{total_prefectures}] 📍 {kanji} ({romaji})")
            print("-" * 60)
            
            try:
                # Get elections
                elections = self._get_prefecture_elections(romaji, kanji)
                
                if elections:
                    print(f"  ✓ Found {len(elections)} elections")
                    
                    # Process each election
                    for election_idx, election_url in enumerate(elections, 1):
                        if election_idx % 10 == 0:
                            print(f"  Progress: {election_idx}/{len(elections)} elections", end="\r", flush=True)
                        
                        try:
                            politicians = self._extract_politicians_from_election(election_url, kanji)
                            if politicians:
                                all_politicians.extend(politicians)
                                
                                # Auto-save every 1000 records
                                if len(all_politicians) % 1000 == 0:
                                    print(f"\n  💾 Auto-saving {len(all_politicians):,} records...")
                                    exporter.export(all_politicians, output_file)
                        
                        except Exception as e:
                            print(f"\n  ⚠️  Error in election {election_idx}: {e}")
                            continue
                    
                    print(f"  ✓ Collected {len([p for p in all_politicians if p['prefecture'] == kanji])} politicians")
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Interrupted by user - saving progress...")
                if all_politicians:
                    exporter.export(all_politicians, output_file)
                    print(f"💾 Saved {len(all_politicians):,} politicians to {output_file}")
                raise
            
            except Exception as e:
                print(f"  ❌ Error: {e}")
                continue
        
        # Final save
        if all_politicians:
            print(f"\n{'='*80}")
            print("💾 Saving final results...")
            exporter.export(all_politicians, output_file)
        
        # Stats
        elapsed = time.time() - start_time
        print(f"\n{'='*80}")
        print("📊 SCRAPING COMPLETE")
        print(f"{'='*80}")
        print(f"Total politicians: {len(all_politicians):,}")
        print(f"Total requests: {self.total_requests:,}")
        print(f"  - Cached: {self.cached_requests:,} ({self.cached_requests/max(self.total_requests,1)*100:.1f}%)")
        print(f"  - New: {self.new_requests:,} ({self.new_requests/max(self.total_requests,1)*100:.1f}%)")
        print(f"Time elapsed: {elapsed/60:.1f} minutes")
        print(f"Average speed: {len(all_politicians)/(elapsed/60):.0f} politicians/minute")
        print(f"Output: data/outputs/{output_file}")
        print(f"{'='*80}\n")
        
        return all_politicians


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fast election data scraper")
    parser.add_argument(
        '--output', '-o',
        default='politicians_from_elections_FULL.csv',
        help='Output CSV filename'
    )
    parser.add_argument(
        '--delay-cached',
        type=float,
        default=0.1,
        help='Delay for cached requests (default: 0.1s)'
    )
    parser.add_argument(
        '--delay-new',
        type=float,
        default=1.0,
        help='Delay for new requests (default: 1.0s)'
    )
    
    args = parser.parse_args()
    
    # Extract just filename if full path given
    output_filename = Path(args.output).name
    
    try:
        scraper = FastElectionScraper(
            delay_cached=args.delay_cached,
            delay_new=args.delay_new
        )
        politicians = scraper.scrape_all_elections(output_filename)
        
        print(f"\n✅ Success! Collected {len(politicians):,} politicians")
        print(f"📁 Saved to: data/outputs/{output_filename}\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
        print("Progress has been saved. You can restart to continue.\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
