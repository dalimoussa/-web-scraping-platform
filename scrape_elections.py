"""
Election Data Scraper - Extract Politician Names from Election Results
選挙結果から政治家情報を抽出

Strategy: Scrape election results pages to build politician database.
Election results are public information, so lower risk than politician profiles.
"""

import sys
from pathlib import Path
import re
from typing import List, Dict, Any, Set
from urllib.parse import urljoin
import time

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.http_client import HTTPClient
from src.core.csv_exporter import CSVExporter
from src.utils.parsers import parse_html
from datetime import datetime


class ElectionDataScraper:
    """
    Scraper for election results to extract politician information.
    
    This approach scrapes PUBLIC ELECTION RESULTS rather than politician profiles,
    which has lower terms-of-service risk.
    """
    
    def __init__(self, delay: float = 3.0):
        """Initialize scraper with respectful delay."""
        self.http = HTTPClient(default_delay=delay, use_cache=True, respect_robots_txt=True)
        self.base_url = "https://seijiyama.jp"
        self.elections_base = f"{self.base_url}/elections"
        
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
    
    def scrape_all_elections(self, limit_per_prefecture: int = None) -> List[Dict[str, Any]]:
        """
        Scrape election data from all prefectures.
        
        Args:
            limit_per_prefecture: Maximum elections per prefecture
            
        Returns:
            List of politician records extracted from elections
        """
        
        print("\n" + "="*80)
        print("🗳️  ELECTION DATA SCRAPER - 選挙データ収集")
        print("   Strategy: Extract politician names from election results")
        print("   Lower TOS risk - election results are public information")
        print("="*80 + "\n")
        
        all_politicians = []
        seen_names = set()  # Deduplicate politicians
        
        total_prefectures = len(self.prefectures)
        
        for idx, (romaji, kanji) in enumerate(self.prefectures, 1):
            print(f"\n[{idx}/{total_prefectures}] 📍 {kanji} ({romaji})")
            print("-" * 60)
            
            try:
                # Get elections for this prefecture
                elections = self._get_prefecture_elections(romaji, kanji)
                
                if elections:
                    print(f"  ✓ Found {len(elections)} elections")
                    
                    # Limit elections if specified
                    elections_to_scrape = elections[:limit_per_prefecture] if limit_per_prefecture else elections
                    
                    # Extract politicians from each election
                    for election_idx, election_url in enumerate(elections_to_scrape, 1):
                        print(f"  [{election_idx}/{len(elections_to_scrape)}] ", end="", flush=True)
                        
                        try:
                            politicians = self._extract_politicians_from_election(election_url, kanji)
                            
                            # Add new politicians (deduplicate by name)
                            new_count = 0
                            for politician in politicians:
                                name = politician.get('name')
                                if name and name not in seen_names:
                                    seen_names.add(name)
                                    all_politicians.append(politician)
                                    new_count += 1
                            
                            print(f"✓ {len(politicians)} candidates ({new_count} new)")
                            
                        except Exception as e:
                            print(f"✗ Error: {str(e)[:40]}")
                        
                        # Be respectful - delay between elections
                        time.sleep(1)
                else:
                    print(f"  ⚠ No elections found")
                
            except Exception as e:
                print(f"  ✗ Error accessing {kanji}: {str(e)[:50]}")
            
            # Delay between prefectures
            time.sleep(2)
            
            # Show progress
            print(f"  📊 Total politicians collected so far: {len(all_politicians)}")
        
        print("\n" + "="*80)
        print(f"✅ SCRAPING COMPLETE! Collected {len(all_politicians)} unique politicians")
        print("="*80 + "\n")
        
        return all_politicians
    
    def _get_prefecture_elections(self, romaji: str, kanji: str) -> List[str]:
        """Get list of election URLs for a prefecture."""
        
        # Try prefecture page
        prefecture_url = f"{self.elections_base}/pref/{romaji}/"
        
        try:
            response = self.http.get(prefecture_url)
            # Use response.content.decode to avoid encoding issues
            html_content = response.content.decode('utf-8', errors='replace')
            soup = parse_html(html_content)
            
            election_links = []
            
            # Find election links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                
                # Look for election card/detail pages
                if '/area/card/' in href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in election_links:
                        election_links.append(full_url)
            
            return election_links
            
        except Exception as e:
            print(f"    Error getting elections: {e}")
            return []
    
    def _extract_politicians_from_election(self, election_url: str, prefecture: str) -> List[Dict[str, Any]]:
        """
        Extract candidate information from an election page.
        
        Args:
            election_url: URL of the election results page
            prefecture: Prefecture name
            
        Returns:
            List of politician dictionaries
        """
        
        try:
            response = self.http.get(election_url)
            # Use response.content.decode to avoid encoding issues
            html_content = response.content.decode('utf-8', errors='replace')
            soup = parse_html(html_content)
            
            politicians = []
            
            # Extract election name
            election_name = ""
            title_tag = soup.find('h1') or soup.find('h2')
            if title_tag:
                election_name = title_tag.get_text(strip=True)
            
            # Extract election date
            election_date = self._extract_date_from_page(soup)
            
            # Look for candidate tables
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) < 1:
                        continue
                    
                    # Extract candidate name
                    for cell in cells:
                        text = cell.get_text(strip=True)
                        
                        # Look for Japanese names (2-5 characters with kanji/hiragana)
                        if self._is_likely_candidate_name(text):
                            politician = {
                                'name': text,
                                'prefecture': prefecture,
                                'election': election_name,
                                'election_date': election_date,
                                'source': 'seijiyama.jp/elections',
                                'source_url': election_url,
                                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            
                            # Try to extract party (often in nearby cell)
                            party = self._extract_party_from_row(row)
                            if party:
                                politician['party'] = party
                            
                            # Try to extract status (当選/elected, 落選/defeated)
                            status = self._extract_election_status(row)
                            if status:
                                politician['status'] = status
                            
                            # Try to extract vote count
                            votes = self._extract_vote_count(row)
                            if votes:
                                politician['votes'] = votes
                            
                            politicians.append(politician)
            
            # Also look for candidate lists in div/li elements
            candidate_divs = soup.find_all(['div', 'li'], class_=re.compile(r'candidate|person|member', re.I))
            
            for div in candidate_divs:
                name = self._extract_name_from_element(div)
                if name and self._is_likely_candidate_name(name):
                    politician = {
                        'name': name,
                        'prefecture': prefecture,
                        'election': election_name,
                        'election_date': election_date,
                        'source': 'seijiyama.jp/elections',
                        'source_url': election_url,
                        'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Extract additional info
                    party = self._extract_party_from_element(div)
                    if party:
                        politician['party'] = party
                    
                    politicians.append(politician)
            
            return politicians
            
        except Exception as e:
            raise Exception(f"Failed to extract from {election_url}: {e}")
    
    def _is_likely_candidate_name(self, text: str) -> bool:
        """Check if text looks like a candidate name."""
        
        if not text or len(text) < 2 or len(text) > 8:
            return False
        
        # Must contain kanji or hiragana
        if not re.search(r'[\u4e00-\u9fff\u3040-\u309f]', text):
            return False
        
        # Exclude common non-name text
        exclude_patterns = [
            r'選挙', r'投票', r'結果', r'候補', r'当選', r'落選',
            r'市長', r'知事', r'議員', r'月', r'日', r'年',
            r'票', r'得票', r'開票', r'確定', r'速報',
            r'無所属', r'政党', r'支持', r'推薦'
        ]
        
        for pattern in exclude_patterns:
            if re.search(pattern, text):
                return False
        
        return True
    
    def _extract_name_from_element(self, element) -> str:
        """Extract candidate name from HTML element."""
        
        # Try name-specific tags first
        name_tag = element.find(class_=re.compile(r'name', re.I))
        if name_tag:
            return name_tag.get_text(strip=True)
        
        # Otherwise return element text
        return element.get_text(strip=True).split()[0] if element.get_text(strip=True) else ""
    
    def _extract_party_from_row(self, row) -> str:
        """Extract party affiliation from table row."""
        
        cells = row.find_all(['td', 'th'])
        
        for cell in cells:
            text = cell.get_text(strip=True)
            
            # Check for common party names
            parties = [
                '自民', '自由民主党', '立憲', '立憲民主党', '公明', '公明党',
                '共産', '共産党', '国民民主', '維新', '日本維新の会',
                '社民', '社会民主党', 'れいわ', 'れいわ新選組',
                'NHK党', 'NHKから国民を守る党', '無所属'
            ]
            
            for party in parties:
                if party in text:
                    return text
        
        return ""
    
    def _extract_party_from_element(self, element) -> str:
        """Extract party from HTML element."""
        
        party_tag = element.find(class_=re.compile(r'party|affiliation|所属', re.I))
        if party_tag:
            return party_tag.get_text(strip=True)
        
        # Check element text for party keywords
        text = element.get_text()
        parties = [
            '自民', '立憲', '公明', '共産', '国民民主', '維新',
            '社民', 'れいわ', 'NHK党', '無所属'
        ]
        
        for party in parties:
            if party in text:
                return party
        
        return ""
    
    def _extract_election_status(self, row) -> str:
        """Extract election result status (当選/落選)."""
        
        text = row.get_text()
        
        if '当選' in text or '当' in text:
            return '当選'
        elif '落選' in text or '落' in text:
            return '落選'
        
        return ""
    
    def _extract_vote_count(self, row) -> str:
        """Extract vote count from row."""
        
        cells = row.find_all(['td', 'th'])
        
        for cell in cells:
            text = cell.get_text(strip=True)
            
            # Look for numbers that might be vote counts
            if re.match(r'^\d{1,10}$', text):
                return text
        
        return ""
    
    def _extract_date_from_page(self, soup) -> str:
        """Extract election date from page."""
        
        # Look for date patterns in text
        text = soup.get_text()
        
        # Pattern: YYYY年MM月DD日
        date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
        if date_match:
            year, month, day = date_match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Pattern: YYYY/MM/DD
        date_match = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', text)
        if date_match:
            year, month, day = date_match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        return ""


def main():
    """Main function."""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Scrape politician data from election results'
    )
    parser.add_argument(
        '--prefectures', '-p',
        nargs='+',
        help='Specific prefectures to scrape (romaji names)'
    )
    parser.add_argument(
        '--limit-per-prefecture', '-l',
        type=int,
        help='Maximum elections per prefecture'
    )
    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=3.0,
        help='Delay between requests in seconds (default: 3.0)'
    )
    parser.add_argument(
        '--output', '-o',
        default='election_politicians.csv',
        help='Output CSV file'
    )
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = ElectionDataScraper(delay=args.delay)
    
    # Filter prefectures if specified
    if args.prefectures:
        scraper.prefectures = [
            (romaji, kanji) for romaji, kanji in scraper.prefectures
            if romaji in args.prefectures
        ]
        print(f"\n📍 Limiting to {len(scraper.prefectures)} prefectures: {', '.join(args.prefectures)}\n")
    
    # Scrape elections
    politicians = scraper.scrape_all_elections(
        limit_per_prefecture=args.limit_per_prefecture
    )
    
    if politicians:
        # Save to CSV
        exporter = CSVExporter()
        output_path = exporter.export(politicians, args.output)
        
        print("\n" + "="*80)
        print("📊 FINAL STATISTICS")
        print("="*80)
        print(f"\n✅ Total unique politicians: {len(politicians)}")
        
        # Count by prefecture
        from collections import Counter
        prefecture_counts = Counter(p.get('prefecture') for p in politicians)
        print(f"\n📍 Top prefectures:")
        for pref, count in prefecture_counts.most_common(10):
            print(f"  • {pref}: {count} politicians")
        
        # Count by party
        party_counts = Counter(p.get('party', '不明') for p in politicians if p.get('party'))
        if party_counts:
            print(f"\n🏛️  Top parties:")
            for party, count in party_counts.most_common(10):
                print(f"  • {party}: {count} politicians")
        
        # Data quality
        with_party = sum(1 for p in politicians if p.get('party'))
        with_status = sum(1 for p in politicians if p.get('status'))
        with_date = sum(1 for p in politicians if p.get('election_date'))
        
        print(f"\n📈 Data quality:")
        print(f"  • With party: {with_party} ({with_party/len(politicians)*100:.1f}%)")
        print(f"  • With election result: {with_status} ({with_status/len(politicians)*100:.1f}%)")
        print(f"  • With election date: {with_date} ({with_date/len(politicians)*100:.1f}%)")
        
        print(f"\n📁 Output: {output_path}\n")
        
        # Show sample
        print("📋 Sample politicians:")
        for i, p in enumerate(politicians[:10], 1):
            print(f"\n{i}. {p.get('name', 'N/A')}")
            if p.get('party'):
                print(f"   Party: {p.get('party')}")
            if p.get('prefecture'):
                print(f"   Prefecture: {p.get('prefecture')}")
            if p.get('election'):
                print(f"   Election: {p.get('election')}")
            if p.get('status'):
                print(f"   Result: {p.get('status')}")
        
        print("\n" + "="*80)
        print("✅ ELECTION DATA SCRAPING COMPLETE!")
        print("="*80 + "\n")
        
    else:
        print("\n❌ No politician data extracted.")
        print("\n💡 Troubleshooting:")
        print("  1. Check if seijiyama.jp/elections/ is accessible")
        print("  2. Review HTML structure of election pages")
        print("  3. Try with specific prefectures: --prefectures tokyo osaka")
        print("  4. Increase delay: --delay 5.0\n")


if __name__ == "__main__":
    main()
