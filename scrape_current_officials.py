"""
Current Officials Scraper - Collect CURRENTLY SERVING public officials
目標: 国会議員 + 都道府県議会議員 + 主要市議会議員 = 5,000-10,000 officials

This scraper focuses on CURRENT officials to maximize data quality.
Source: seijiyama.jp/member/ (public official directory)
"""

import sys
from pathlib import Path
import re
from typing import List, Dict, Any
from urllib.parse import urljoin
import time

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.http_client import HTTPClient
from src.core.csv_exporter import CSVExporter
from src.utils.parsers import parse_html
from datetime import datetime


class CurrentOfficialsScraper:
    """
    Scraper for currently serving public officials.
    
    Targets:
    1. National Diet (国会) - House of Representatives + House of Councillors (~700 members)
    2. Prefectural Assemblies (都道府県議会) - All 47 prefectures (~2,500 members)
    3. Major City Councils (市議会) - Top 20 cities (~1,000 members)
    
    Total target: 4,000-5,000 current officials
    """
    
    def __init__(self, delay: float = 2.0):
        """Initialize scraper with respectful delay."""
        self.http = HTTPClient(default_delay=delay, use_cache=True, respect_robots_txt=True)
        self.base_url = "https://seijiyama.jp"
        self.members_base = f"{self.base_url}/member"
        
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
        
        # Major cities to scrape city council members
        self.major_cities = [
            "tokyo", "yokohama", "osaka", "nagoya", "sapporo",
            "fukuoka", "kobe", "kyoto", "kawasaki", "saitama",
            "hiroshima", "sendai", "kitakyushu", "chiba", "sakai",
            "niigata", "hamamatsu", "kumamoto", "sagamihara", "shizuoka"
        ]
    
    def scrape_all_officials(self) -> List[Dict[str, Any]]:
        """
        Scrape all current officials.
        
        Returns:
            List of official records
        """
        
        print("\n" + "="*80)
        print("👔 CURRENT OFFICIALS SCRAPER - 現職公務員データ収集")
        print("   Target: National Diet + Prefectural Assemblies + Major Cities")
        print("   Expected: 4,000-5,000 current officials")
        print("="*80 + "\n")
        
        all_officials = []
        
        # 1. Scrape National Diet members
        print("\n" + "="*80)
        print("📍 PHASE 1: NATIONAL DIET MEMBERS (国会議員)")
        print("="*80)
        national_officials = self._scrape_national_diet()
        all_officials.extend(national_officials)
        print(f"✅ Collected {len(national_officials)} national diet members\n")
        
        # 2. Scrape Prefectural Assembly members
        print("\n" + "="*80)
        print("📍 PHASE 2: PREFECTURAL ASSEMBLY MEMBERS (都道府県議会議員)")
        print("="*80)
        prefectural_officials = self._scrape_prefectural_assemblies()
        all_officials.extend(prefectural_officials)
        print(f"✅ Collected {len(prefectural_officials)} prefectural assembly members\n")
        
        # 3. Scrape Major City Council members
        print("\n" + "="*80)
        print("📍 PHASE 3: MAJOR CITY COUNCIL MEMBERS (主要市議会議員)")
        print("="*80)
        city_officials = self._scrape_city_councils()
        all_officials.extend(city_officials)
        print(f"✅ Collected {len(city_officials)} city council members\n")
        
        print("\n" + "="*80)
        print(f"✅ SCRAPING COMPLETE! Collected {len(all_officials)} current officials")
        print("="*80 + "\n")
        
        return all_officials
    
    def _scrape_national_diet(self) -> List[Dict[str, Any]]:
        """Scrape National Diet members (House of Representatives + House of Councillors)."""
        
        officials = []
        
        # House of Representatives (衆議院)
        print("\n[1/2] 🏛️  House of Representatives (衆議院)")
        print("-" * 60)
        hr_url = f"{self.members_base}/kokkai/shugiin/"
        hr_members = self._scrape_member_list(hr_url, "National", "House of Representatives")
        officials.extend(hr_members)
        print(f"  ✓ Found {len(hr_members)} representatives")
        
        # House of Councillors (参議院)
        print("\n[2/2] 🏛️  House of Councillors (参議院)")
        print("-" * 60)
        hc_url = f"{self.members_base}/kokkai/sangiin/"
        hc_members = self._scrape_member_list(hc_url, "National", "House of Councillors")
        officials.extend(hc_members)
        print(f"  ✓ Found {len(hc_members)} councillors")
        
        return officials
    
    def _scrape_prefectural_assemblies(self) -> List[Dict[str, Any]]:
        """Scrape all prefectural assembly members."""
        
        officials = []
        total_prefectures = len(self.prefectures)
        
        for idx, (romaji, kanji) in enumerate(self.prefectures, 1):
            print(f"\n[{idx}/{total_prefectures}] 📍 {kanji} ({romaji})")
            print("-" * 60)
            
            try:
                # Prefectural assembly URL
                pref_url = f"{self.members_base}/pref/{romaji}/"
                members = self._scrape_member_list(pref_url, kanji, "Prefectural Assembly")
                officials.extend(members)
                print(f"  ✓ Found {len(members)} assembly members")
                
            except Exception as e:
                print(f"  ✗ Error: {str(e)[:50]}")
            
            time.sleep(1)  # Brief delay between prefectures
        
        return officials
    
    def _scrape_city_councils(self) -> List[Dict[str, Any]]:
        """Scrape major city council members."""
        
        officials = []
        total_cities = len(self.major_cities)
        
        for idx, city in enumerate(self.major_cities, 1):
            print(f"\n[{idx}/{total_cities}] 🏙️  {city.title()}")
            print("-" * 60)
            
            try:
                # City council URL
                city_url = f"{self.members_base}/city/{city}/"
                members = self._scrape_member_list(city_url, city.title(), "City Council")
                officials.extend(members)
                print(f"  ✓ Found {len(members)} council members")
                
            except Exception as e:
                print(f"  ✗ Error: {str(e)[:50]}")
            
            time.sleep(1)  # Brief delay between cities
        
        return officials
    
    def _scrape_member_list(self, url: str, jurisdiction: str, office_type: str) -> List[Dict[str, Any]]:
        """
        Scrape a list of members from a URL.
        
        Args:
            url: URL of the member list page
            jurisdiction: Prefecture/city/national
            office_type: Type of office
            
        Returns:
            List of official dictionaries
        """
        
        try:
            response = self.http.get(url)
            html_content = response.content.decode('utf-8', errors='replace')
            soup = parse_html(html_content)
            
            members = []
            
            # Look for member links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                
                # Look for individual member profile pages
                if '/member/detail/' in href or '/person/' in href:
                    member_url = urljoin(self.base_url, href)
                    
                    # Extract member info from the link or surrounding context
                    name = link.get_text(strip=True)
                    
                    if name and len(name) >= 2 and len(name) <= 10:
                        member = {
                            'name': name,
                            'jurisdiction': jurisdiction,
                            'office_type': office_type,
                            'status': 'Current',  # These are current officials
                            'source': 'seijiyama.jp/member',
                            'source_url': member_url,
                            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        members.append(member)
            
            # Also try to extract from tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    for cell in cells:
                        text = cell.get_text(strip=True)
                        if self._is_likely_official_name(text):
                            member = {
                                'name': text,
                                'jurisdiction': jurisdiction,
                                'office_type': office_type,
                                'status': 'Current',
                                'source': 'seijiyama.jp/member',
                                'source_url': url,
                                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            members.append(member)
            
            # Deduplicate by name
            seen = set()
            unique_members = []
            for member in members:
                if member['name'] not in seen:
                    seen.add(member['name'])
                    unique_members.append(member)
            
            return unique_members
            
        except Exception as e:
            print(f"    Error scraping {url}: {e}")
            return []
    
    def _is_likely_official_name(self, text: str) -> bool:
        """Check if text looks like an official's name."""
        
        if not text or len(text) < 2 or len(text) > 10:
            return False
        
        # Must contain Japanese characters
        if not re.search(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]', text):
            return False
        
        # Exclude common non-name patterns
        exclude = ['氏名', '名前', '議員', '代表', '選挙', '投票', '結果', '一覧']
        for keyword in exclude:
            if keyword in text:
                return False
        
        return True


def main():
    """Main function."""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape current public officials')
    parser.add_argument(
        '--delay',
        type=float,
        default=2.0,
        help='Delay between requests in seconds (default: 2.0)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/outputs/current_officials.csv',
        help='Output CSV file'
    )
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = CurrentOfficialsScraper(delay=args.delay)
    
    # Scrape officials
    officials = scraper.scrape_all_officials()
    
    if officials:
        # Save to CSV
        exporter = CSVExporter()
        # Extract just the filename if full path provided
        output_filename = Path(args.output).name if '/' in args.output or '\\' in args.output else args.output
        output_path = exporter.export(officials, output_filename)
        
        print("\n" + "="*80)
        print("📊 FINAL STATISTICS")
        print("="*80)
        print(f"\n✅ Total current officials: {len(officials)}")
        
        # Count by jurisdiction
        from collections import Counter
        jurisdiction_counts = Counter(o.get('jurisdiction') for o in officials)
        print(f"\n📍 By jurisdiction:")
        for jurisdiction, count in jurisdiction_counts.most_common():
            print(f"  • {jurisdiction}: {count} officials")
        
        # Count by office type
        office_counts = Counter(o.get('office_type') for o in officials)
        print(f"\n🏛️  By office type:")
        for office, count in office_counts.most_common():
            print(f"  • {office}: {count} officials")
        
        print(f"\n💾 Saved to: {output_path}")
        print("\n" + "="*80)
        print("✅ SCRAPING COMPLETE!")
        print("="*80 + "\n")
    else:
        print("\n⚠️  No officials collected")


if __name__ == "__main__":
    main()
