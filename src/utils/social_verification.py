"""
Social media verification detection utilities.
Detects verification badges from HTML without API access.
"""

from typing import Optional, Dict
import re

from ..utils.parsers import parse_html
from ..core.logger import get_logger


logger = get_logger(__name__)


# Platform-specific verification patterns
VERIFICATION_PATTERNS = {
    'x': [
        # Twitter/X verified badge
        r'aria-label="Verified account"',
        r'data-testid="icon-verified"',
        r'<svg[^>]*verified[^>]*>',
        r'class="[^"]*verified-badge[^"]*"',
        r'Verified account',
    ],
    
    'instagram': [
        # Instagram verified badge
        r'aria-label="Verified"',
        r'class="[^"]*verified-badge[^"]*"',
        r'title="Verified"',
        r'coreSpriteVerifiedBadge',
        r'<svg[^>]*verified[^>]*>',
    ],
    
    'facebook': [
        # Facebook verified badge
        r'aria-label="Verified Page"',
        r'class="[^"]*verified-badge[^"]*"',
        r'<i[^>]*verified[^>]*>',
        r'Verified Page',
    ],
    
    'youtube': [
        # YouTube verified badge
        r'aria-label="Verified"',
        r'class="[^"]*badge-style-type-verified[^"]*"',
        r'<svg[^>]*verified[^>]*>',
        r'yt-icon-verified',
    ],
}


def detect_verification(html: str, platform: str) -> Optional[bool]:
    """
    Detect if account is verified from HTML.
    
    Args:
        html: Page HTML content
        platform: Platform name (x, instagram, facebook, youtube)
        
    Returns:
        True if verified, False if not, None if unknown
    """
    if not html or platform not in VERIFICATION_PATTERNS:
        return None
    
    patterns = VERIFICATION_PATTERNS[platform]
    
    for pattern in patterns:
        if re.search(pattern, html, re.IGNORECASE):
            logger.debug(f"Verification badge detected for {platform}")
            return True
    
    # Check for explicit "not verified" indicators
    not_verified_patterns = [
        r'Not verified',
        r'Unverified account',
    ]
    
    for pattern in not_verified_patterns:
        if re.search(pattern, html, re.IGNORECASE):
            logger.debug(f"Account explicitly not verified for {platform}")
            return False
    
    # If no clear indication, return None
    return None


def detect_follower_count(html: str, platform: str) -> Optional[int]:
    """
    Extract follower count from HTML.
    
    Args:
        html: Page HTML content
        platform: Platform name
        
    Returns:
        Follower count or None
    """
    if not html:
        return None
    
    # Platform-specific patterns
    follower_patterns = {
        'x': [
            r'(\d+(?:,\d+)*(?:\.\d+)?[KMB]?)\s*(?:Followers|followers)',
            r'data-count="(\d+)".*followers',
        ],
        'instagram': [
            r'(\d+(?:,\d+)*(?:\.\d+)?[KMB]?)\s*(?:followers|フォロワー)',
            r'"edge_followed_by":\s*{\s*"count":\s*(\d+)',
        ],
        'facebook': [
            r'(\d+(?:,\d+)*(?:\.\d+)?[KMB]?)\s*(?:followers|likes)',
        ],
        'youtube': [
            r'(\d+(?:,\d+)*(?:\.\d+)?[KMB]?)\s*(?:subscribers|登録者)',
            r'"subscriberCountText".*?"simpleText":\s*"([^"]+)"',
        ],
    }
    
    patterns = follower_patterns.get(platform, [])
    
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            count_str = match.group(1)
            return _parse_count(count_str)
    
    return None


def _parse_count(count_str: str) -> Optional[int]:
    """
    Parse follower count string to integer.
    
    Args:
        count_str: Count string like "1.2M", "500K", "1,234"
        
    Returns:
        Integer count or None
    """
    if not count_str:
        return None
    
    # Remove commas
    count_str = count_str.replace(',', '')
    
    # Handle K, M, B suffixes
    multipliers = {
        'K': 1_000,
        'M': 1_000_000,
        'B': 1_000_000_000,
    }
    
    for suffix, multiplier in multipliers.items():
        if count_str.upper().endswith(suffix):
            try:
                number = float(count_str[:-1])
                return int(number * multiplier)
            except ValueError:
                return None
    
    # Plain number
    try:
        return int(float(count_str))
    except ValueError:
        return None


def enhance_social_profile(
    profile_url: str,
    platform: str,
    html: Optional[str] = None,
    http_client = None,
) -> Dict:
    """
    Enhance social profile with verification and follower count.
    
    Args:
        profile_url: Profile URL
        platform: Platform name
        html: Pre-fetched HTML (fetches if None)
        http_client: HTTP client for fetching
        
    Returns:
        Dict with verified and follower_count
    """
    result = {
        'verified': None,
        'follower_count': None,
    }
    
    # Fetch HTML if not provided
    if html is None and http_client:
        try:
            response = http_client.get_safe(profile_url)
            if response:
                html = response.text
        except Exception as e:
            logger.warning(f"Failed to fetch {profile_url}: {e}")
            return result
    
    if not html:
        return result
    
    # Detect verification
    result['verified'] = detect_verification(html, platform)
    
    # Detect follower count
    result['follower_count'] = detect_follower_count(html, platform)
    
    return result
