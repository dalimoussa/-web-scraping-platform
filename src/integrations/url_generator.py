"""
Municipal URL Generator - Generate official website URLs from Japanese city names.
Handles romanization, common patterns, and validates generated URLs.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin
import requests
from pathlib import Path
import json

try:
    from pykakasi import kakasi
    PYKAKASI_AVAILABLE = True
except ImportError:
    PYKAKASI_AVAILABLE = False
    logging.warning("pykakasi not installed - romanization will be limited to known cities only")

logger = logging.getLogger(__name__)

# Romanization mapping for Japanese characters (Hepburn)
HIRAGANA_TO_ROMAJI = {
    'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
    'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
    'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
    'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
    'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
    'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
    'だ': 'da', 'ぢ': 'ji', 'づ': 'zu', 'で': 'de', 'ど': 'do',
    'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
    'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
    'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
    'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
    'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
    'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
    'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
    'わ': 'wa', 'ゐ': 'wi', 'ゑ': 'we', 'を': 'wo', 'ん': 'n',
    'きゃ': 'kya', 'きゅ': 'kyu', 'きょ': 'kyo',
    'しゃ': 'sha', 'しゅ': 'shu', 'しょ': 'sho',
    'ちゃ': 'cha', 'ちゅ': 'chu', 'ちょ': 'cho',
    'にゃ': 'nya', 'にゅ': 'nyu', 'にょ': 'nyo',
    'ひゃ': 'hya', 'ひゅ': 'hyu', 'ひょ': 'hyo',
    'みゃ': 'mya', 'みゅ': 'myu', 'みょ': 'myo',
    'りゃ': 'rya', 'りゅ': 'ryu', 'りょ': 'ryo',
    'ぎゃ': 'gya', 'ぎゅ': 'gyu', 'ぎょ': 'gyo',
    'じゃ': 'ja', 'じゅ': 'ju', 'じょ': 'jo',
    'びゃ': 'bya', 'びゅ': 'byu', 'びょ': 'byo',
    'ぴゃ': 'pya', 'ぴゅ': 'pyu', 'ぴょ': 'pyo',
}

# Known romanizations for major cities (kanji → romaji)
KNOWN_CITIES = {
    # Hokkaido
    '札幌市': 'sapporo', '函館市': 'hakodate', '旭川市': 'asahikawa', '小樽市': 'otaru',
    '釧路市': 'kushiro', '帯広市': 'obihiro', '北見市': 'kitami', '室蘭市': 'muroran',
    
    # Tohoku
    '青森市': 'aomori', '八戸市': 'hachinohe', '弘前市': 'hirosaki',
    '盛岡市': 'morioka', '仙台市': 'sendai', '石巻市': 'ishinomaki',
    '秋田市': 'akita', '山形市': 'yamagata', '福島市': 'fukushima', '郡山市': 'koriyama',
    
    # Kanto
    '東京都': 'tokyo', '横浜市': 'yokohama', '川崎市': 'kawasaki', '相模原市': 'sagamihara',
    'さいたま市': 'saitama', '千葉市': 'chiba', '船橋市': 'funabashi',
    '宇都宮市': 'utsunomiya', '前橋市': 'maebashi', '高崎市': 'takasaki', '水戸市': 'mito',
    
    # Chubu
    '新潟市': 'niigata', '長岡市': 'nagaoka', '富山市': 'toyama', '金沢市': 'kanazawa',
    '福井市': 'fukui', '甲府市': 'kofu', '長野市': 'nagano', '松本市': 'matsumoto',
    '岐阜市': 'gifu', '静岡市': 'shizuoka', '浜松市': 'hamamatsu', '名古屋市': 'nagoya',
    '豊田市': 'toyota', '岡崎市': 'okazaki',
    
    # Kansai
    '津市': 'tsu', '大津市': 'otsu', '京都市': 'kyoto', '大阪市': 'osaka',
    '堺市': 'sakai', '東大阪市': 'higashiosaka', '神戸市': 'kobe', '姫路市': 'himeji',
    '奈良市': 'nara', '和歌山市': 'wakayama',
    
    # Chugoku/Shikoku
    '鳥取市': 'tottori', '松江市': 'matsue', '岡山市': 'okayama', '倉敷市': 'kurashiki',
    '広島市': 'hiroshima', '福山市': 'fukuyama', '下関市': 'shimonoseki', '山口市': 'yamaguchi',
    '徳島市': 'tokushima', '高松市': 'takamatsu', '松山市': 'matsuyama', '高知市': 'kochi',
    
    # Kyushu/Okinawa
    '北九州市': 'kitakyushu', '福岡市': 'fukuoka', '久留米市': 'kurume',
    '佐賀市': 'saga', '長崎市': 'nagasaki', '佐世保市': 'sasebo',
    '熊本市': 'kumamoto', '大分市': 'oita', '宮崎市': 'miyazaki', '鹿児島市': 'kagoshima',
    '那覇市': 'naha',
}

# Prefecture romanizations
PREFECTURES = {
    '北海道': 'hokkaido', '青森県': 'aomori', '岩手県': 'iwate', '宮城県': 'miyagi',
    '秋田県': 'akita', '山形県': 'yamagata', '福島県': 'fukushima',
    '茨城県': 'ibaraki', '栃木県': 'tochigi', '群馬県': 'gunma', '埼玉県': 'saitama',
    '千葉県': 'chiba', '東京都': 'tokyo', '神奈川県': 'kanagawa',
    '新潟県': 'niigata', '富山県': 'toyama', '石川県': 'ishikawa', '福井県': 'fukui',
    '山梨県': 'yamanashi', '長野県': 'nagano', '岐阜県': 'gifu', '静岡県': 'shizuoka',
    '愛知県': 'aichi', '三重県': 'mie',
    '滋賀県': 'shiga', '京都府': 'kyoto', '大阪府': 'osaka', '兵庫県': 'hyogo',
    '奈良県': 'nara', '和歌山県': 'wakayama',
    '鳥取県': 'tottori', '島根県': 'shimane', '岡山県': 'okayama', '広島県': 'hiroshima',
    '山口県': 'yamaguchi',
    '徳島県': 'tokushima', '香川県': 'kagawa', '愛媛県': 'ehime', '高知県': 'kochi',
    '福岡県': 'fukuoka', '佐賀県': 'saga', '長崎県': 'nagasaki', '熊本県': 'kumamoto',
    '大分県': 'oita', '宮崎県': 'miyazaki', '鹿児島県': 'kagoshima', '沖縄県': 'okinawa',
}


class MunicipalURLGenerator:
    """Generate municipal website URLs from Japanese city names."""
    
    def __init__(self, validate_urls: bool = True):
        """
        Initialize URL generator.
        
        Args:
            validate_urls: Whether to validate generated URLs (slower but accurate)
        """
        self.validate_urls = validate_urls
        self.logger = logging.getLogger(__name__)
        self.url_cache = {}
        
        # Initialize pykakasi for romanization
        if PYKAKASI_AVAILABLE:
            self.kks = kakasi()
        else:
            self.kks = None
            self.logger.warning("pykakasi not available - using fallback romanization")
        
        self.load_cache()
    
    def load_cache(self):
        """Load cached URL mappings."""
        cache_file = Path('data/url_cache.json')
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.url_cache = json.load(f)
                self.logger.info(f"Loaded {len(self.url_cache)} cached URLs")
            except Exception as e:
                self.logger.warning(f"Could not load URL cache: {e}")
    
    def save_cache(self):
        """Save URL mappings to cache."""
        cache_file = Path('data/url_cache.json')
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.url_cache, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Saved {len(self.url_cache)} URLs to cache")
        except Exception as e:
            self.logger.error(f"Could not save URL cache: {e}")
    
    def generate_url(
        self,
        city_name: str,
        prefecture: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Generate official website URL from city name.
        
        Args:
            city_name: Japanese city name (e.g., "旭川市", "札幌市")
            prefecture: Japanese prefecture name (optional, for disambiguation)
            
        Returns:
            Dict with url, confidence, method, and alternatives
        """
        # Check cache first
        cache_key = f"{prefecture}_{city_name}" if prefecture else city_name
        if cache_key in self.url_cache:
            return self.url_cache[cache_key]
        
        # Remove suffixes (市, 区, 町, 村, 都, 道, 府, 県)
        clean_name = re.sub(r'[市区町村都道府県]$', '', city_name)
        clean_prefecture = re.sub(r'[都道府県]$', '', prefecture) if prefecture else None
        
        # Get romanization
        romaji = self.romanize(clean_name)
        prefecture_romaji = self.romanize(clean_prefecture) if clean_prefecture else None
        
        # Generate candidate URLs
        candidates = self._generate_candidates(
            city_name,
            romaji,
            prefecture,
            prefecture_romaji
        )
        
        # Validate URLs if enabled
        if self.validate_urls:
            best_url = self._validate_candidates(candidates)
        else:
            best_url = candidates[0] if candidates else None
        
        result = {
            'city_name': city_name,
            'prefecture': prefecture,
            'url': best_url['url'] if best_url else None,
            'confidence': best_url['confidence'] if best_url else 'low',
            'method': best_url['method'] if best_url else 'guess',
            'romaji': romaji,
            'alternatives': [c['url'] for c in candidates[:3]],
            'validated': self.validate_urls,
        }
        
        # Cache result
        self.url_cache[cache_key] = result
        
        return result
    
    def romanize(self, japanese_text: str) -> str:
        """
        Convert Japanese text to romaji.
        
        Args:
            japanese_text: Japanese text (kanji/hiragana/katakana)
            
        Returns:
            Romanized text
        """
        if not japanese_text:
            return ''
        
        # Check if in known cities (manual database has priority - more accurate)
        if japanese_text in KNOWN_CITIES:
            return KNOWN_CITIES[japanese_text]
        
        # Check if in prefectures
        if japanese_text in PREFECTURES:
            return PREFECTURES[japanese_text]
        
        # Use pykakasi for automatic romanization
        if self.kks:
            try:
                result = self.kks.convert(japanese_text)
                # Join all romanized parts
                romaji = ''.join([item['hepburn'] for item in result])
                return romaji.strip()
            except Exception as e:
                self.logger.warning(f"pykakasi romanization failed for {japanese_text}: {e}")
        
        # Fallback: use original text
        self.logger.warning(f"Unknown romanization for: {japanese_text}")
        return japanese_text
    
    def _generate_candidates(
        self,
        city_name: str,
        romaji: str,
        prefecture: Optional[str],
        prefecture_romaji: Optional[str],
    ) -> List[Dict[str, any]]:
        """Generate candidate URLs based on common patterns."""
        candidates = []
        
        # Pattern 1: https://www.city.{romaji}.lg.jp (most common)
        candidates.append({
            'url': f"https://www.city.{romaji}.lg.jp",
            'confidence': 'high',
            'method': 'pattern1',
        })
        
        # Pattern 2: https://www.city.{romaji}.{prefecture}.jp
        if prefecture_romaji:
            candidates.append({
                'url': f"https://www.city.{romaji}.{prefecture_romaji}.jp",
                'confidence': 'high',
                'method': 'pattern2',
            })
        
        # Pattern 3: https://www.{romaji}.lg.jp
        candidates.append({
            'url': f"https://www.{romaji}.lg.jp",
            'confidence': 'medium',
            'method': 'pattern3',
        })
        
        # Pattern 4: https://{romaji}.lg.jp
        candidates.append({
            'url': f"https://{romaji}.lg.jp",
            'confidence': 'medium',
            'method': 'pattern4',
        })
        
        # Pattern 5: https://www.{romaji}.{prefecture}.jp
        if prefecture_romaji:
            candidates.append({
                'url': f"https://www.{romaji}.{prefecture_romaji}.jp",
                'confidence': 'medium',
                'method': 'pattern5',
            })
        
        # Pattern 6: Special cases for wards (区)
        if '区' in city_name:
            ward_name = romaji.replace('ku', '')
            candidates.append({
                'url': f"https://www.city.{ward_name}.lg.jp",
                'confidence': 'low',
                'method': 'pattern6_ward',
            })
        
        return candidates
    
    def _validate_candidates(self, candidates: List[Dict]) -> Optional[Dict]:
        """
        Validate candidate URLs by checking if they're accessible.
        
        Args:
            candidates: List of candidate URL dicts
            
        Returns:
            Best valid URL or None
        """
        for candidate in candidates:
            url = candidate['url']
            
            try:
                # Quick HEAD request to check if URL exists
                response = requests.head(url, timeout=5, allow_redirects=True)
                
                if response.status_code == 200:
                    self.logger.info(f"✓ Valid URL found: {url}")
                    candidate['confidence'] = 'verified'
                    return candidate
                elif response.status_code in [301, 302]:
                    # Follow redirect
                    self.logger.info(f"→ Redirect found: {url}")
                    candidate['url'] = response.headers.get('Location', url)
                    candidate['confidence'] = 'verified'
                    return candidate
                    
            except requests.RequestException as e:
                self.logger.debug(f"✗ Invalid URL: {url} ({e})")
                continue
        
        # No valid URL found, return best guess
        if candidates:
            self.logger.warning(f"No valid URL found, using best guess: {candidates[0]['url']}")
            return candidates[0]
        
        return None
    
    def batch_generate(
        self,
        municipalities: List[Dict[str, str]],
        save_progress: bool = True,
    ) -> List[Dict[str, any]]:
        """
        Generate URLs for multiple municipalities.
        
        Args:
            municipalities: List of dicts with 'city_name' and 'prefecture'
            save_progress: Whether to save progress periodically
            
        Returns:
            List of URL generation results
        """
        results = []
        total = len(municipalities)
        
        for idx, muni in enumerate(municipalities, 1):
            city_name = muni.get('municipality_name') or muni.get('city_name', '')
            prefecture = muni.get('prefecture', '')
            
            self.logger.info(f"[{idx}/{total}] Generating URL for {city_name}, {prefecture}")
            
            result = self.generate_url(city_name, prefecture)
            result['row_number'] = muni.get('row_number', idx)
            results.append(result)
            
            # Save progress every 100 items
            if save_progress and idx % 100 == 0:
                self.save_cache()
                self.logger.info(f"Progress saved: {idx}/{total} completed")
        
        # Final save
        if save_progress:
            self.save_cache()
        
        return results


# Convenience function
def generate_municipal_urls(
    municipalities: List[Dict[str, str]],
    validate: bool = False,
) -> List[Dict[str, any]]:
    """
    Generate official website URLs from municipality names.
    
    Args:
        municipalities: List of dicts with 'city_name' and 'prefecture'
        validate: Whether to validate URLs (slower but accurate)
        
    Returns:
        List of URL generation results
        
    Example:
        >>> munis = [
        ...     {'city_name': '旭川市', 'prefecture': '北海道'},
        ...     {'city_name': '函館市', 'prefecture': '北海道'},
        ... ]
        >>> results = generate_municipal_urls(munis, validate=True)
        >>> print(results[0]['url'])
        'https://www.city.asahikawa.hokkaido.jp'
    """
    generator = MunicipalURLGenerator(validate_urls=validate)
    return generator.batch_generate(municipalities)
