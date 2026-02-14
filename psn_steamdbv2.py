# Updated psn_steamdbv2.py with release date scraping
import json
import time
import logging
import re
import requests
import sys
import random
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from urllib.parse import urljoin, quote, urlparse
from dataclasses import dataclass
from bs4 import BeautifulSoup
import urllib3
import cloudscraper


# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('steamdb_psn_scraper.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global imports for Selenium
HAS_SELENIUM = False
HAS_UC = False
HAS_WEBDRIVER_MANAGER = False

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
    from selenium.webdriver.support.ui import Select
    HAS_SELENIUM = True
    logger.info("✅ Selenium imported successfully")
except ImportError as e:
    logger.error(f"❌ Selenium import failed: {e}")
    logger.error("Install with: pip install selenium")
    HAS_SELENIUM = False

try:
    import undetected_chromedriver as uc
    HAS_UC = True
    logger.info("✅ undetected_chromedriver imported successfully")
except ImportError as e:
    logger.warning(f"⚠️  undetected_chromedriver not available: {e}")
    logger.warning("Install with: pip install undetected-chromedriver")
    HAS_UC = False

try:
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_WEBDRIVER_MANAGER = True
    logger.info("✅ webdriver_manager imported successfully")
except ImportError as e:
    logger.warning(f"⚠️  webdriver_manager not available: {e}")
    logger.warning("Install with: pip install webdriver-manager")
    HAS_WEBDRIVER_MANAGER = False


# ===========================================
# RELEASE DATE EXTRACTION FUNCTION
# ===========================================

def extract_release_date_from_psn_page(html_content):
    """
    Extract release date from PSN store page HTML with flexible layout.
    Handles different languages and responsive designs.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Strategy 1: Look for the release date using data-qa attributes
        release_date_key = None
        
        # Find all dt elements that might contain release date label
        dt_elements = soup.find_all('dt')
        
        # Possible release date keys in different languages
        # Finnish: "Julkaisu:", English: "Release Date:", etc.
        release_date_labels = [
            'Julkaisu:', 'Julkaisu', 'Release Date:', 'Release Date',
            'Release:', 'Release', 'Data di pubblicazione:', '発売日:',
            'Fecha de lanzamiento:', 'Veröffentlichungsdatum:',
            'Дата выхода:', '출시일:', 'تاريخ الإصدار:'
        ]
        
        # Look for matching dt element
        for dt in dt_elements:
            dt_text = dt.get_text(strip=True)
            if any(label.lower() in dt_text.lower() for label in release_date_labels):
                # Found the label, now get the corresponding dd element
                parent = dt.parent
                if parent:
                    # Find the next dd element after this dt
                    dt_index = dt.parent.findChildren().index(dt) if dt.parent else -1
                    if dt_index != -1:
                        children = parent.findChildren()
                        if dt_index + 1 < len(children):
                            dd = children[dt_index + 1]
                            release_date = dd.get_text(strip=True)
                            if release_date:
                                # Clean up the date format
                                release_date = release_date.replace('\n', ' ').strip()
                                return release_date
        
        # Strategy 2: Look for data-qa attributes specifically for release date
        release_dd = soup.find('dd', {'data-qa': 'gameInfo#releaseInformation#releaseDate-value'})
        if release_dd:
            release_date = release_dd.get_text(strip=True)
            if release_date:
                return release_date
        
        # Strategy 3: Look for platform release date section
        release_section = soup.find('dl', {'data-qa': 'gameInfo#releaseInformation'})
        if release_section:
            # Find all dt/dd pairs
            dts = release_section.find_all('dt')
            dds = release_section.find_all('dd')
            
            for dt, dd in zip(dts, dds):
                dt_text = dt.get_text(strip=True)
                if any(label.lower() in dt_text.lower() for label in release_date_labels):
                    release_date = dd.get_text(strip=True)
                    if release_date:
                        return release_date
        
        # Strategy 4: Search for date patterns in the game info section
        date_patterns = [
            r'\d{1,2}\.\d{1,2}\.\d{4}',  # dd.mm.yyyy (Finnish format)
            r'\d{4}-\d{2}-\d{2}',        # yyyy-mm-dd
            r'\d{1,2}/\d{1,2}/\d{4}',    # mm/dd/yyyy
            r'\d{1,2}\s+[A-Za-zäöüß]+\s+\d{4}',  # 20 October 2023
        ]
        
        # Search in the game info section
        game_info = soup.find('div', {'data-qa': 'gameInfo'})
        if game_info:
            text_content = game_info.get_text()
            for pattern in date_patterns:
                match = re.search(pattern, text_content)
                if match:
                    return match.group()
        
        return None
        
    except Exception as e:
        logger.error(f"Error extracting release date: {e}")
        return None


@dataclass
class PSNGame:
    """Data class for PSN game information"""
    title_id: str
    name: str
    url: str
    price: str
    original_price: Optional[str] = None
    discount_percent: Optional[str] = None
    platform_tags: List[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    release_date: Optional[str] = None
    developer: Optional[str] = None
    publisher: Optional[str] = None
    rating: Optional[str] = None
    matched_steam_game: Optional[Dict] = None
    match_confidence: float = 0.0
    game_type: str = "Unknown"
    store_display_classification: Optional[str] = None
    sku_id: Optional[str] = None  # Added SKU ID field
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'title_id': self.title_id,
            'name': self.name,
            'url': self.url,
            'price': self.price,
            'original_price': self.original_price,
            'discount_percent': self.discount_percent,
            'platform_tags': self.platform_tags or [],
            'image_url': self.image_url,
            'description': self.description,
            'release_date': self.release_date,
            'developer': self.developer,
            'publisher': self.publisher,
            'rating': self.rating,
            'match_confidence': self.match_confidence,
            'game_type': self.game_type,
            'store_display_classification': self.store_display_classification,
            'sku_id': self.sku_id,  # Include SKU ID in dictionary
            'matched_steam_game': self.matched_steam_game
        }


class PSNScraper:
    """PSN Store Scraper with Cloudflare bypass"""
    
    def __init__(self, region: str = 'fi-fi', platform_filter: str = None):
        """
        Initialize PSN scraper with Cloudflare bypass
        
        Args:
            region: PSN region (e.g., 'fi-fi', 'en-us', 'en-gb')
            platform_filter: Filter by platform ('ps4', 'ps5', 'both', or None for all)
        """
        self.region = region
        self.platform_filter = platform_filter.lower() if platform_filter else None
        self.base_url = f'https://store.playstation.com/{region}'
        
        # Use cloudscraper to bypass Cloudflare
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            },
            delay=10,
            interpreter='nodejs'
        )
        
        # Update headers
        self.scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'fi-FI,fi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
        
        logger.info(f"Initialized PSNScraper for region: {region}, platform filter: {self.platform_filter}")

    def update_with_cf_clearance(self, cf_clearance_value):
        """
        Update the scraper session with cf_clearance cookie
        
        Args:
            cf_clearance_value: The cf_clearance cookie value
        
        Returns:
            bool: True if successful
        """
        try:
            # Update headers with cookie
            cookie_header = f"cf_clearance={cf_clearance_value}"
            
            # Add to existing cookies if any
            if 'Cookie' in self.scraper.headers:
                existing_cookies = self.scraper.headers['Cookie']
                if 'cf_clearance' not in existing_cookies:
                    self.scraper.headers['Cookie'] = f"{existing_cookies}; {cookie_header}"
            else:
                self.scraper.headers['Cookie'] = cookie_header
            
            logger.info("Added cf_clearance cookie to requests session")
            return True
            
        except Exception as e:
            logger.error(f"Error adding cf_clearance cookie: {e}")
            return False

    def get_game_release_date(self, url: str, game_name: str = None) -> Optional[str]:
        """
        Get release date for a specific game by URL.
        
        Args:
            url: The PSN game page URL
            game_name: Optional game name for logging
        
        Returns:
            Release date string or None if not found
        """
        try:
            logger.info(f"Fetching release date for: {game_name or 'Unknown game'}")
            
            # Make the request
            response = self.scraper.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch game page {url}: {response.status_code}")
                return None
            
            # Extract release date
            release_date = extract_release_date_from_psn_page(response.text)
            
            if release_date and game_name:
                logger.info(f"Found release date for '{game_name}': {release_date}")
            elif not release_date and game_name:
                logger.debug(f"No release date found for '{game_name}'")
            
            return release_date
            
        except Exception as e:
            logger.error(f"Error getting release date for {url}: {e}")
            return None

    def search_games_with_release_dates(self, query: str, max_results: int = 20) -> List[PSNGame]:
        """
        Search for games and fetch their release dates.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
        
        Returns:
            List of PSNGame objects with release_date attribute
        """
        # First search for games
        games = self.search_games_with_pagination(query, max_results)
        
        if not games:
            return games
        
        logger.info(f"Fetching release dates for {len(games)} games...")
        
        # Fetch release dates for each game
        for i, game in enumerate(games):
            try:
                # Check if we already have a release date from the search
                if not game.release_date or game.release_date == 'N/A':
                    # Fetch release date from game page
                    release_date = self.get_game_release_date(game.url, game.name)
                    if release_date:
                        game.release_date = release_date
                    
                    # Add small delay to avoid rate limiting
                    if i < len(games) - 1:
                        time.sleep(1)  # 1 second delay between requests
                        
            except Exception as e:
                logger.error(f"Error getting release date for {game.name}: {e}")
                continue
        
        # Count games with release dates
        games_with_dates = sum(1 for game in games if game.release_date and game.release_date != 'N/A')
        logger.info(f"Found release dates for {games_with_dates} out of {len(games)} games")

        # Re-apply sort so Full Game always leads even after release-date fetching
        games = self._sort_by_type_priority(games)

        return games
    
    def _extract_sku_id(self, apollo_state: Dict, product_id: str) -> Optional[str]:
        """
        Extract SKU ID from Apollo state data
        
        Args:
            apollo_state: The Apollo state dictionary from the page JSON
            product_id: The product ID to find SKU for
            
        Returns:
            SKU ID string or None
        """
        try:
            # Method 1: Look for SKU entries in the cache
            for key, value in apollo_state.items():
                if key.startswith('Sku:') and isinstance(value, dict):
                    # Check if this SKU is related to the product
                    sku_id = key.replace('Sku:', '')
                    # If the SKU ID contains the product ID, it's likely the right one
                    if product_id in sku_id:
                        logger.debug(f"Found SKU ID from cache key: {sku_id}")
                        return sku_id
            
            # Method 2: Look in product data for SKU references
            product_key = f"Product:{product_id}"
            if product_key in apollo_state:
                product_data = apollo_state[product_key]
                # Check if skus field exists
                if 'skus' in product_data and isinstance(product_data['skus'], list):
                    for sku_ref in product_data['skus']:
                        if isinstance(sku_ref, dict) and '__ref' in sku_ref:
                            sku_key = sku_ref['__ref']
                            if sku_key.startswith('Sku:'):
                                sku_id = sku_key.replace('Sku:', '')
                                logger.debug(f"Found SKU ID from product reference: {sku_id}")
                                return sku_id
            
            # Method 3: Search for SKU pattern in JSON string
            json_str = json.dumps(apollo_state)
            sku_pattern = r'"sku[Ii]d?":\s*"([^"]+)"'
            matches = re.findall(sku_pattern, json_str)
            if matches:
                logger.debug(f"Found SKU ID from pattern search: {matches[0]}")
                return matches[0]
            
            logger.debug(f"No SKU ID found for product {product_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting SKU ID: {e}")
            return None
    
    def _matches_platform_filter(self, game: PSNGame) -> bool:
        """
        Check if game matches the platform filter
        
        Args:
            game: PSNGame object
        
        Returns:
            True if game matches platform filter or no filter is set
        """
        if not self.platform_filter or self.platform_filter == 'both':
            return True
        
        if not game.platform_tags:
            return False
        
        # Convert platform tags to lowercase for comparison
        platform_tags_lower = [tag.lower() for tag in game.platform_tags]
        
        # Check for platform matches
        if self.platform_filter == 'ps4':
            return any('ps4' in tag or 'playstation 4' in tag for tag in platform_tags_lower)
        elif self.platform_filter == 'ps5':
            return any('ps5' in tag or 'playstation 5' in tag for tag in platform_tags_lower)
        
        return False
    
    def _determine_game_type(self, store_display_classification: str, localized_store_display_classification: str, name: str) -> str:
        """Determine the type of game based on classification data"""
        game_type = "Unknown"
        
        # Check store_display_classification first
        if store_display_classification:
            store_display_classification = store_display_classification.upper()
            if store_display_classification == "FULL_GAME":
                game_type = "Full Game"
            elif store_display_classification == "ADD_ON":
                game_type = "Add-on"
            elif store_display_classification == "PREMIUM_ADD_ON":
                game_type = "Premium Add-on"
            elif store_display_classification == "DEMO":
                game_type = "Demo"
            elif store_display_classification == "TRIAL":
                game_type = "Trial"
            elif store_display_classification == "BUNDLE":
                game_type = "Bundle"
            elif store_display_classification == "THEME":
                game_type = "Theme"
            elif store_display_classification == "AVATAR":
                game_type = "Avatar"
            elif store_display_classification == "SUBSCRIPTION":
                game_type = "Subscription"
            elif store_display_classification == "EDITION":
                game_type = "Edition"
            elif store_display_classification == "UNKNOWN":
                pass
        
        # Check localized classification for additional info
        if localized_store_display_classification:
            localized_lower = localized_store_display_classification.lower()
            
            # Finnish classifications
            if "kokonainen" in localized_lower and "peli" in localized_lower:
                game_type = "Full Game"
            elif "lisäosa" in localized_lower or "liite" in localized_lower:
                game_type = "Add-on"
            elif "demo" in localized_lower:
                game_type = "Demo"
            elif "kokeilu" in localized_lower or "koe" in localized_lower:
                game_type = "Trial"
            elif "paketti" in localized_lower or "kokoelma" in localized_lower:
                game_type = "Bundle"
            elif "teema" in localized_lower:
                game_type = "Theme"
            elif "avatar" in localized_lower:
                game_type = "Avatar"
            elif "tilaus" in localized_lower:
                game_type = "Subscription"
            elif "versio" in localized_lower or "painos" in localized_lower:
                game_type = "Edition"
            
            # English classifications
            elif "full game" in localized_lower:
                game_type = "Full Game"
            elif "add-on" in localized_lower or "dlc" in localized_lower:
                game_type = "Add-on"
            elif "bundle" in localized_lower:
                game_type = "Bundle"
            elif "theme" in localized_lower:
                game_type = "Theme"
            elif "avatar" in localized_lower:
                game_type = "Avatar"
            elif "subscription" in localized_lower:
                game_type = "Subscription"
            elif "demo" in localized_lower:
                game_type = "Demo"
            elif "trial" in localized_lower:
                game_type = "Trial"
            elif "edition" in localized_lower:
                game_type = "Edition"
        
        # Additional checks based on game name patterns
        name_lower = name.lower()
        name_upper = name.upper()

        # ── Virtual currency / in-game packs (highest priority catch) ──────────
        # These must be checked BEFORE generic add-on/DLC patterns because PSN
        # search often surfaces them first even when the user wants the full game.
        _currency_keywords = [
            # Generic currency
            'coins', 'credits', 'tokens', 'gems', 'gold', 'silver', 'cash',
            'bucks', 'points', 'stars', 'diamonds', 'crystals', 'rubies',
            'currency', 'wallet', 'funds',
            # Common franchise currencies
            'v-bucks', 'apex coins', 'shark card', 'shark cash', 'moon credits',
            'rainbow coins', 'cells', 'astral diamonds', 'platinum', 'gil',
            'zenny', 'munny', 'florins', 'kreds', 'rep', 'orbs', 'essence',
            'shards', 'dust', 'crowns', 'seeds', 'leaves', 'berries',
            # Pack / bundle patterns that indicate content packs not full games
            'starter pack', 'starter bundle', 'founders pack', 'season pass',
            'character pack', 'skin pack', 'costume pack', 'cosmetic',
            'booster pack', 'item pack', 'loot pack', 'resource pack',
            'virtual currency', 'in-game currency', 'digital currency',
        ]
        _pack_patterns = [
            r'\b\d+[kK]?\s*(coins?|credits?|tokens?|gems?|gold|bucks?|points?|diamonds?)\b',
            r'\b(small|medium|large|huge|massive|mega|ultra|supreme|epic|legendary|starter)\s+(pack|bundle|bag|chest|box|pouch)\b',
            r'\bpack\s+of\s+\d+\b',
            r'\b\d+[,\s]\d{3}\s+(coins?|credits?|tokens?)\b',
        ]

        if game_type not in ("Add-on", "Premium Add-on"):
            name_lower_check = name_lower
            if any(kw in name_lower_check for kw in _currency_keywords):
                game_type = "Virtual Currency"
            else:
                for pat in _pack_patterns:
                    if re.search(pat, name_lower_check):
                        game_type = "Virtual Currency"
                        break

        # Check for obvious indicators
        if game_type not in ("Virtual Currency",):
            if 'DLC' in name_upper or 'ADD-ON' in name_upper or 'EXPANSION' in name_upper:
                game_type = "Add-on"
            elif 'THEME' in name_upper or 'teema' in name_lower:
                game_type = "Theme"
            elif 'AVATAR' in name_upper or 'avatar' in name_lower:
                game_type = "Avatar"
            elif 'BUNDLE' in name_upper or 'paketti' in name_lower or 'kokoelma' in name_lower:
                game_type = "Bundle"
            elif 'EDITION' in name_upper and game_type != "Add-on":
                game_type = "Edition"
        
        # Final safety check
        if game_type == "Unknown":
            game_terms = ['game', 'peli', 'assassin', 'creed', 'odyssey', 'valhalla']
            if any(term in name_lower for term in game_terms):
                game_type = "Full Game"
        
        return game_type
    
    # ── Priority order for PSN result sorting ─────────────────────────────────
    _GAME_TYPE_PRIORITY = {
        "Full Game":        0,
        "Edition":          1,   # GOTY / Deluxe editions of a full game
        "Bundle":           2,   # Multi-game bundles
        "Demo":             3,
        "Trial":            4,
        "Add-on":           5,
        "Premium Add-on":   6,
        "Subscription":     7,
        "Theme":            8,
        "Avatar":           9,
        "Virtual Currency": 10,  # currency packs / item packs go last
        "Unknown":          11,
    }

    def _sort_by_type_priority(self, games: List['PSNGame']) -> List['PSNGame']:
        """Return games sorted so Full Game results appear before add-ons / currency packs."""
        return sorted(
            games,
            key=lambda g: self._GAME_TYPE_PRIORITY.get(g.game_type, 10)
        )

    def search_games_with_pagination(self, query: str, max_results: int = 200, platform_filter: str = None) -> List['PSNGame']:
        """Search for games on PSN Store with pagination, Cloudflare bypass, and platform filtering"""
        if platform_filter:
            self.platform_filter = platform_filter.lower()
        
        encoded_query = quote(query)
        all_games = []
        page = 1
        
        logger.info(f"Searching PSN for: '{query}', platform filter: {self.platform_filter}")
        
        while len(all_games) < max_results:
            if page == 1:
                url = f"{self.base_url}/search/{encoded_query}"
            else:
                url = f"{self.base_url}/search/{encoded_query}/{page}"
            
            logger.info(f"Search URL (page {page}): {url}")
            
            try:
                # Use cloudscraper with retry
                response = self.scraper.get(url, timeout=30)
                
                # Check for 404
                if response.status_code == 404:
                    logger.info(f"Received 404 for page {page}, stopping pagination")
                    break
                
                response.raise_for_status()
                
                # Parse the page
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to extract JSON data
                script_tags = soup.find_all('script')
                json_data = None
                
                for script in script_tags:
                    if script.string and '"search:results"' in script.string:
                        try:
                            start_idx = script.string.find('{"props"')
                            if start_idx != -1:
                                json_str = script.string[start_idx:]
                                end_idx = json_str.find('</script>')
                                if end_idx != -1:
                                    json_str = json_str[:end_idx]
                                json_data = json.loads(json_str)
                                break
                        except json.JSONDecodeError as e:
                            logger.warning(f"JSON parse error on page {page}: {e}")
                
                if json_data:
                    # Extract games from JSON
                    try:
                        games_data = json_data.get('props', {}).get('apolloState', {})
                        
                        current_page_games = []
                        for key, value in games_data.items():
                            if isinstance(value, dict) and 'name' in value:
                                # Pass apollo_state to parsing method for SKU extraction
                                game_info = self._parse_product_from_json(value, apollo_state=games_data)
                                if game_info:
                                    # Apply platform filter if specified
                                    if self._matches_platform_filter(game_info):
                                        current_page_games.append(game_info)
                        
                        if not current_page_games:
                            logger.info(f"No games found on page {page} (after platform filtering), stopping")
                            break
                        
                        all_games.extend(current_page_games)
                        logger.info(f"Parsed {len(current_page_games)} games from page {page} (platform filter: {self.platform_filter})")
                        
                        # Check if we should continue
                        if len(current_page_games) < 24:
                            logger.info(f"Less than 24 games on page {page}, stopping pagination")
                            break
                        
                        page += 1
                        time.sleep(random.uniform(1, 2))  # Random delay
                        
                    except Exception as e:
                        logger.error(f"Error parsing page {page}: {e}")
                        break
                else:
                    # Fallback to HTML parsing
                    current_page_games = self._parse_search_results_html(response.text, max_results - len(all_games))
                    if current_page_games:
                        all_games.extend(current_page_games)
                        logger.info(f"Parsed {len(current_page_games)} games from page {page} (HTML fallback)")
                        
                        if len(current_page_games) < 24:
                            logger.info(f"Less than 24 games on page {page}, stopping pagination")
                            break
                        
                        page += 1
                        time.sleep(random.uniform(1, 2))
                    else:
                        logger.info(f"No games found on page {page}, stopping")
                        break
                        
            except Exception as e:
                logger.error(f"Request error on page {page}: {e}")
                break
        
        logger.info(f"Total games found across {page-1} pages: {len(all_games)}")
        
        # Log statistics
        game_type_counts = {}
        for game in all_games:
            game_type_counts[game.game_type] = game_type_counts.get(game.game_type, 0) + 1
        
        logger.info(f"Game type statistics: {game_type_counts}")

        # Sort so Full Game results always come first, currency/add-on packs last
        all_games = self._sort_by_type_priority(all_games)
        logger.info("Results re-sorted by game type priority (Full Game first)")

        return all_games[:max_results]
    
    def search_games(self, query: str, max_results: int = 50, platform_filter: str = None) -> List[PSNGame]:
        """
        Search for games on PSN Store (wrapper for backward compatibility)
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            platform_filter: Filter by platform ('ps4', 'ps5', 'both', or None)
            
        Returns:
            List of PSNGame objects
        """
        return self.search_games_with_pagination(query, max_results, platform_filter)
    
    def _parse_search_results_html(self, html: str, max_results: int) -> List[PSNGame]:
        """
        Parse search results HTML (fallback method)
        
        Args:
            html: HTML content
            max_results: Maximum number of results to parse
            
        Returns:
            List of PSNGame objects
        """
        games = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for the JSON data first
        script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
        if script_tag:
            try:
                json_data = json.loads(script_tag.string)
                # Extract product IDs from the JSON
                apollo_state = json_data.get('props', {}).get('apolloState', {})
                
                # Look for Product references
                for key, value in apollo_state.items():
                    if isinstance(value, dict) and value.get('__typename') == 'Product':
                        game = self._parse_product_from_json(value, apollo_state=apollo_state)
                        if game and len(games) < max_results:
                            games.append(game)
            except Exception as e:
                logger.error(f"Error extracting JSON from script: {e}")
        
        # If no games from JSON, fall back to HTML parsing
        if not games:
            # Find all product tiles
            product_selectors = [
                '[data-qa^="search#productTile"]',
                '[data-qa*="productTile"]',
                '.psw-product-tile',
                'a[data-telemetry-meta*="id"]'
            ]
            
            product_elements = []
            for selector in product_selectors:
                product_elements = soup.select(selector)
                if product_elements:
                    logger.info(f"Found {len(product_elements)} product elements with selector: {selector}")
                    break
            
            if not product_elements:
                # Try alternative parsing
                product_elements = soup.find_all('a', href=lambda x: x and '/product/' in x)
                logger.info(f"Found {len(product_elements)} product elements via href parsing")
            
            for i, element in enumerate(product_elements[:max_results]):
                try:
                    game = self._parse_product_element(element)
                    if game:
                        games.append(game)
                except Exception as e:
                    logger.error(f"Error parsing product element {i}: {e}")
                    continue
        
        return games
    
    def normalize_game_name(self, name: str) -> str:
        """
        Normalize game name for matching
        
        Args:
            name: Original game name
            
        Returns:
            Normalized name
        """
        # Remove special characters, extra spaces, convert to lowercase
        normalized = name.lower()
        normalized = re.sub(r'[^\w\s]', '', normalized)  # Remove punctuation
        normalized = re.sub(r'\s+', ' ', normalized).strip()  # Normalize spaces
        
        # Remove common suffixes
        suffixes = ['definitive edition', 'remastered', 'deluxe edition', 
                   'game of the year', 'goty', 'edition', 'enhanced edition',
                   'complete edition', 'ultimate edition']
        
        for suffix in suffixes:
            normalized = re.sub(r'\s+' + re.escape(suffix) + r'$', '', normalized)
        
        return normalized
    
    def _parse_product_from_json(self, product_data: Dict, apollo_state: Dict = None) -> Optional[PSNGame]:
        """
        Parse a product from JSON data
        
        Args:
            product_data: JSON product data from Apollo state
            
            apollo_state: Full Apollo state dictionary for SKU extraction
        Returns:
            PSNGame object or None
        """
        try:
            # Extract basic information
            product_id = product_data.get('id', '')
            name = product_data.get('name', '')
            np_title_id = product_data.get('npTitleId', '')
            
            
            # Extract SKU ID if apollo_state is available
            sku_id = None
            if apollo_state and product_id:
                sku_id = self._extract_sku_id(apollo_state, product_id)
            
            if not name:
                return None
            
            # Extract classification information
            store_display_classification = product_data.get('storeDisplayClassification', '')
            localized_store_display_classification = product_data.get('localizedStoreDisplayClassification', '')
            
            # Determine game type
            game_type = self._determine_game_type(
                store_display_classification,
                localized_store_display_classification,
                name
            )
            
            # Extract price information
            price_data = product_data.get('price', {})
            base_price = price_data.get('basePrice', 'N/A')
            discounted_price = price_data.get('discountedPrice', 'N/A')
            discount_text = price_data.get('discountText', '')
            
            # Determine which price to show
            display_price = discounted_price if discounted_price != 'N/A' else base_price
            
            # Calculate discount percentage if available
            discount_percent = None
            if discount_text and '%' in discount_text:
                discount_match = re.search(r'([\d.]+)%', discount_text)
                if discount_match:
                    discount_percent = discount_match.group(1)
            
            # Extract platforms
            platforms = product_data.get('platforms', [])
            
            # Extract release date
            release_date = None
            # Try different possible fields for release date
            release_date = product_data.get('releaseDate', None)
            if not release_date:
                release_date = product_data.get('originalReleaseDate', None)
            if release_date:
                # Format the date if it's a timestamp
                try:
                    from datetime import datetime
                    if isinstance(release_date, (int, float)):
                        release_date = datetime.fromtimestamp(release_date / 1000).strftime('%d.%m.%Y')
                    elif isinstance(release_date, str) and 'T' in release_date:
                        # ISO format date
                        dt = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
                        release_date = dt.strftime('%d.%m.%Y')
                except:
                    pass  # Keep original format if parsing fails
            
            # Extract media URLs
            media = product_data.get('media', [])
            image_url = None
            for media_item in media:
                if media_item.get('type') == 'IMAGE' and media_item.get('role') == 'MASTER':
                    image_url = media_item.get('url', '')
                    break
            
            # Construct URL
            url = f"{self.base_url}/product/{product_id}"
            
            # Create game object
            game = PSNGame(
                title_id=product_id,
                name=name,
                url=url,
                price=display_price,
                original_price=base_price if base_price != discounted_price else None,
                discount_percent=discount_percent,
                platform_tags=platforms,
                image_url=image_url,
                release_date=release_date,
                game_type=game_type,
                store_display_classification=store_display_classification,
                sku_id=sku_id  # Add SKU ID to game object
            )
            
            logger.debug(f"Parsed JSON game: {name} (ID: {product_id}, SKU: {sku_id}, Type: {game_type}, Price: {display_price}, Release: {release_date})")
            return game
            
        except Exception as e:
            logger.error(f"Error parsing product from JSON: {e}")
            logger.debug(f"Product data: {json.dumps(product_data, indent=2)[:500]}...")
            return None
    
    def _parse_product_element(self, element) -> Optional[PSNGame]:
        """
        Parse a single product element
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            PSNGame object or None
        """
        try:
            # Extract data from telemetry meta
            telemetry_meta = element.get('data-telemetry-meta', '{}')
            try:
                meta_data = json.loads(telemetry_meta)
                title_id = meta_data.get('titleId', '')
                game_name = meta_data.get('name', '')
                price = meta_data.get('price', '')
                store_display_classification = meta_data.get('storeDisplayClassification', '')
                localized_store_display_classification = meta_data.get('localizedStoreDisplayClassification', '')
            except:
                title_id = ''
                game_name = ''
                price = ''
                store_display_classification = ''
                localized_store_display_classification = ''
            
            # If name not in meta, try to get it from text
            if not game_name:
                name_elem = element.select_one('[data-qa*="product-name"], #product-name')
                if name_elem:
                    game_name = name_elem.get_text(strip=True)
                else:
                    # Try to get text from the element itself
                    game_name = element.get_text(strip=True)
            
            # Get URL
            url = element.get('href', '')
            if url and not url.startswith('http'):
                url = urljoin(self.base_url, url)
            
            # Extract title ID from URL if not in meta
            if not title_id and url:
                title_match = re.search(r'/product/([^/]+)', url)
                if title_match:
                    title_id = title_match.group(1)
            
            # Get image URL
            image_url = None
            img_elem = element.select_one('img[src*="playstation.com"]')
            if img_elem:
                image_url = img_elem.get('src', '')
                # Clean up thumbnail parameters
                if 'thumb=true' in image_url:
                    image_url = image_url.replace('thumb=true', 'thumb=false')
            
            # Get platform tags
            platform_tags = []
            tag_elements = element.select('.psw-platform-tag, [data-qa*="tag"]')
            for tag in tag_elements:
                platform_text = tag.get_text(strip=True)
                if platform_text:
                    platform_tags.append(platform_text)
            
            # Get discount information
            discount_elem = element.select_one('[data-qa*="discount-badge"]')
            discount_percent = None
            if discount_elem:
                discount_text = discount_elem.get_text(strip=True)
                discount_match = re.search(r'([\d.]+)%', discount_text)
                if discount_match:
                    discount_percent = discount_match.group(1)
            
            # Get original price
            original_price = None
            strikethrough_elem = element.select_one('[data-qa*="price-strikethrough"], s')
            if strikethrough_elem:
                original_price = strikethrough_elem.get_text(strip=True)
            
            # Determine game type
            game_type = self._determine_game_type(
                store_display_classification,
                localized_store_display_classification,
                game_name
            )
            
            # If we still don't have a valid game name, skip
            if not game_name or len(game_name) < 2:
                return None
            
            game = PSNGame(
                title_id=title_id,
                name=game_name,
                url=url,
                price=price or 'N/A',
                original_price=original_price,
                discount_percent=discount_percent,
                platform_tags=platform_tags,
                image_url=image_url,
                game_type=game_type,
                store_display_classification=store_display_classification
            )
            
            logger.debug(f"Parsed PSN game: {game_name} ({title_id}, Type: {game_type})")
            return game
            
        except Exception as e:
            logger.error(f"Error parsing product element: {e}")
            return None
    
    def get_game_details(self, game_url: str) -> Optional[Dict]:
        """
        Get detailed information for a specific game
        
        Args:
            game_url: Game product page URL
            
        Returns:
            Dictionary with game details or None
        """
        try:
            logger.info(f"Fetching game details from: {game_url}")
            response = self.scraper.get(game_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            details = {
                'description': None,
                'release_date': None,
                'developer': None,
                'publisher': None,
                'rating': None,
                'features': [],
                'languages': []
            }
            
            # Extract description
            desc_elem = soup.select_one('[data-qa="mfe-game-overview#description"], .description')
            if desc_elem:
                details['description'] = desc_elem.get_text(strip=True)[:500]  # Limit length
            
            # Extract release date
            # Try multiple selectors for different page layouts
            date_elem = soup.select_one('[data-qa="gameInfo#releaseInformation#releaseDate-value"]')
            if not date_elem:
                date_elem = soup.select_one('[data-qa="gameInfo#releaseInformation#releaseDate"]')
            if date_elem:
                details['release_date'] = date_elem.get_text(strip=True)
            
            # Extract developer and publisher
            info_elements = soup.select('[data-qa*="gameInfo"]')
            for elem in info_elements:
                text = elem.get_text(strip=True)
                if 'Developer:' in text:
                    details['developer'] = text.replace('Developer:', '').strip()
                elif 'Publisher:' in text:
                    details['publisher'] = text.replace('Publisher:', '').strip()
                elif 'PEGI' in text or 'ESRB' in text:
                    details['rating'] = text
            
            # Extract features
            feature_elems = soup.select('[data-qa*="feature"]')
            for elem in feature_elems:
                feature_text = elem.get_text(strip=True)
                if feature_text:
                    details['features'].append(feature_text)
            
            # Extract languages
            lang_elems = soup.select('[data-qa*="language"]')
            for elem in lang_elems:
                lang_text = elem.get_text(strip=True)
                if lang_text:
                    details['languages'].append(lang_text)
            
            return details
            
        except Exception as e:
            logger.error(f"Failed to get game details: {e}")
            return None
    
    def find_matching_game(self, steam_game: Dict, psn_games: List[PSNGame]) -> Tuple[Optional[PSNGame], float]:
        """
        Find the best matching PSN game for a Steam game
        
        Args:
            steam_game: Steam game dictionary
            psn_games: List of PSN games from search results
            
        Returns:
            Tuple of (matched PSN game, confidence score)
        """
        if not psn_games:
            return None, 0.0
        
        steam_name = steam_game.get('name', '').lower()
        steam_name_normalized = self.normalize_game_name(steam_name)
        
        best_match = None
        best_score = 0.0
        
        # First, try to find full games
        full_games = [game for game in psn_games if game.game_type == "Full Game"]
        
        # If no full games found, try all game types
        search_games = full_games if full_games else psn_games
        
        for psn_game in search_games:
            psn_name = psn_game.name.lower()
            psn_name_normalized = self.normalize_game_name(psn_name)
            
            # Calculate similarity score
            score = self._calculate_similarity_score(
                steam_name_normalized, 
                psn_name_normalized,
                steam_name,
                psn_name
            )
            
            # Bonus points for exact platform matches (like "6" in name)
            if steam_name_normalized == psn_name_normalized:
                score += 0.3
            
            # Bonus points for full games
            if psn_game.game_type == "Full Game":
                score += 0.2
            
            # Check for numerical sequences (like "5", "6" in game names)
            steam_numbers = re.findall(r'\d+', steam_name_normalized)
            psn_numbers = re.findall(r'\d+', psn_name_normalized)
            if steam_numbers and psn_numbers and steam_numbers == psn_numbers:
                score += 0.15
            
            # Penalty for different types
            if 'dlc' in psn_name_normalized and 'dlc' not in steam_name_normalized:
                score -= 0.2
            
            # Update best match
            if score > best_score:
                best_score = score
                best_match = psn_game
        
        if best_match and best_score > 0.6:
            best_match.matched_steam_game = steam_game
            best_match.match_confidence = best_score
            return best_match, best_score
        
        return None, 0.0
    
    def _calculate_similarity_score(self, name1: str, name2: str, original1: str, original2: str) -> float:
        """
        Calculate similarity score between two names
        
        Args:
            name1: First normalized name
            name2: Second normalized name
            original1: First original name
            original2: Second original name
            
        Returns:
            Similarity score between 0 and 1
        """
        from difflib import SequenceMatcher
        
        # Basic sequence matcher
        score = SequenceMatcher(None, name1, name2).ratio()
        
        # Boost score if originals are very similar
        original_score = SequenceMatcher(None, original1.lower(), original2.lower()).ratio()
        if original_score > 0.8:
            score = min(1.0, score + 0.2)
        
        # Penalty if lengths differ significantly
        length_diff = abs(len(name1) - len(name2))
        if length_diff > 5:
            score -= min(0.2, length_diff * 0.02)
        
        # Boost if key words match
        key_words1 = set(name1.split())
        key_words2 = set(name2.split())
        common = key_words1.intersection(key_words2)
        if len(common) > 1:
            score += len(common) * 0.1
        
        # Check for series names
        series_keywords = ['assassins creed', 'final fantasy', 'call of duty']
        for keyword in series_keywords:
            if keyword in name1 and keyword in name2:
                score += 0.15
        
        return max(0.0, min(1.0, score))


class SteamDBSeleniumParser:
    """SteamDB parser with Selenium for CAPTCHA handling"""
    
    def __init__(self, headless=True, region='fi-fi', platform_filter: str = None):
        """
        Initialize SteamDB parser
        
        Args:
            headless: Whether to run browser in headless mode
            region: PSN region for PSNScraper
            platform_filter: Filter by platform ('ps4', 'ps5', 'both', or None)
        """
        self.headless = headless
        self.driver = None
        self.base_url = "https://steamdb.info"
        self.platform_filter = platform_filter
        self.psn_scraper = PSNScraper(region=region, platform_filter=platform_filter)
        
        # CAPTCHA handling variables
        self.captcha_detected = False
        self.captcha_url = None
        self.captcha_retries = 0
        self.max_captcha_retries = 3
        self.captcha_wait_time = 30
        
        logger.info(f"Initialized SteamDBSeleniumParser (headless={headless}, platform_filter={platform_filter})")
    
    def search_psn_games_with_release_dates(self, query: str, max_results: int = 20):
        """
        Wrapper method to search PSN games with release dates.
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            List of PSNGame objects
        """
        return self.psn_scraper.search_games_with_release_dates(query, max_results)
    
    def get_release_dates_for_games(self, games: List[Dict]) -> List[Dict]:
        """
        Add release dates to a list of game dictionaries.
        
        Args:
            games: List of game dictionaries
        
        Returns:
            Updated list with release dates
        """
        updated_games = []
        for game in games:
            if 'psn_source' in game and 'url' in game['psn_source']:
                release_date = self.psn_scraper.get_game_release_date(
                    game['psn_source']['url'],
                    game['psn_source']['name']
                )
                if release_date:
                    game['psn_source']['release_date'] = release_date
            updated_games.append(game)
        return updated_games

    def set_platform_filter(self, platform_filter: str):
        """
        Update the platform filter for PSN searches
        
        Args:
            platform_filter: 'ps4', 'ps5', 'both', or None
        """
        self.platform_filter = platform_filter
        self.psn_scraper.platform_filter = platform_filter.lower() if platform_filter else None
        logger.info(f"Updated platform filter to: {platform_filter}")
    
    def _setup_driver(self):
        """Setup ChromeDriver with multiple fallback strategies"""
        if not HAS_SELENIUM:
            logger.error("="*60)
            logger.error("SELENIUM NOT INSTALLED")
            logger.error("="*60)
            logger.error("Install with: pip install selenium")
            logger.error("="*60)
            return False
        
        strategies = []
        
        # Strategy 1: Try undetected_chromedriver (best for anti-detection)
        if HAS_UC:
            strategies.append(("undetected_chromedriver", self._try_undetected_chrome))
        
        # Strategy 2: Try webdriver_manager
        if HAS_WEBDRIVER_MANAGER:
            strategies.append(("webdriver_manager", self._try_webdriver_manager))
        
        # Strategy 3: Try system chromedriver
        strategies.append(("system_chromedriver", self._try_system_chrome))
        
        # Strategy 4: Try Chromium
        strategies.append(("chromium", self._try_chromium))
        
        # Try each strategy
        for strategy_name, strategy_func in strategies:
            try:
                logger.info(f"Attempting Chrome setup with {strategy_name}...")
                if strategy_func():
                    logger.info(f"✅ ChromeDriver setup successful with {strategy_name}")
                    return True
            except Exception as e:
                logger.warning(f"❌ {strategy_name} failed: {str(e)[:100]}")
                continue
        
        # All strategies failed
        logger.error("="*60)
        logger.error("ALL CHROMEDRIVER SETUP STRATEGIES FAILED")
        logger.error("="*60)
        self._print_troubleshooting_guide()
        return False
    
    def _try_undetected_chrome(self):
        """Try setting up with undetected_chromedriver"""
        options = uc.ChromeOptions()
        
        if self.headless:
            options.add_argument('--headless=new')
        
        # Essential arguments
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-extensions')
        
        # Try to create driver
        self.driver = uc.Chrome(options=options, version_main=None)
        
        # Test if it works
        self.driver.get("about:blank")
        return True
    
    def _try_webdriver_manager(self):
        """Try setting up with webdriver_manager"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        # Essential arguments
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-notifications')
        
        # Install and setup driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Anti-detection measures
        try:
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
        except:
            pass  # CDP commands might not work in all environments
        
        # Test if it works
        self.driver.get("about:blank")
        return True
    
    def _try_system_chrome(self):
        """Try setting up with system chromedriver"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        # Essential arguments
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Try common chromedriver locations
        possible_paths = [
            '/usr/bin/chromedriver',
            '/usr/local/bin/chromedriver',
            '/snap/bin/chromium.chromedriver',
            'chromedriver'
        ]
        
        # Try with explicit path first
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    service = Service(executable_path=path)
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    logger.info(f"Using chromedriver at: {path}")
                    self.driver.get("about:blank")
                    return True
                except Exception as e:
                    logger.debug(f"Failed with {path}: {e}")
                    continue
        
        # Try without explicit path (let Selenium find it)
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.get("about:blank")
        return True
    
    def _try_chromium(self):
        """Try setting up with Chromium browser"""
        chrome_options = Options()
        
        # Try common Chromium binary locations
        chromium_paths = [
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
            '/snap/bin/chromium'
        ]
        
        for chromium_path in chromium_paths:
            if os.path.exists(chromium_path):
                chrome_options.binary_location = chromium_path
                logger.info(f"Using Chromium at: {chromium_path}")
                break
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        # Essential arguments for Chromium
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Try with chromedriver
        driver_paths = ['/usr/bin/chromedriver', '/usr/lib/chromium-browser/chromedriver']
        
        for driver_path in driver_paths:
            if os.path.exists(driver_path):
                try:
                    service = Service(executable_path=driver_path)
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    self.driver.get("about:blank")
                    return True
                except:
                    continue
        
        # Try without explicit driver path
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.get("about:blank")
        return True
    
    def _print_troubleshooting_guide(self):
        """Print comprehensive troubleshooting guide"""
        logger.error("")
        logger.error("TROUBLESHOOTING GUIDE:")
        logger.error("")
        logger.error("1. Install Python packages:")
        logger.error("   pip install selenium webdriver-manager undetected-chromedriver")
        logger.error("")
        logger.error("2. Install Chrome (Ubuntu/Debian):")
        logger.error("   wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb")
        logger.error("   sudo apt install ./google-chrome-stable_current_amd64.deb")
        logger.error("")
        logger.error("3. OR Install Chromium:")
        logger.error("   sudo apt update")
        logger.error("   sudo apt install chromium-browser chromium-chromedriver")
        logger.error("")
        logger.error("4. For Streamlit Cloud, create packages.txt with:")
        logger.error("   chromium")
        logger.error("   chromium-driver")
        logger.error("")
        logger.error("5. Test Chrome installation:")
        logger.error("   which google-chrome")
        logger.error("   which chromium-browser")
        logger.error("   which chromedriver")
        logger.error("")
        logger.error("="*60)
    
    def _check_cloudflare(self):
        """Check if Cloudflare challenge is present"""
        try:
            page_source = self.driver.page_source
            return "cloudflare" in page_source.lower() or "challenge" in page_source.lower()
        except:
            return False
    
    def _check_captcha(self):
        """
        Check for various types of CAPTCHA challenges
        Returns: (bool, str) - (is_captcha_present, captcha_type)
        """
        try:
            page_source = self.driver.page_source.lower()
            current_url = self.driver.current_url
            
            # Check for hCaptcha
            if "hcaptcha" in page_source or "h-captcha" in page_source:
                logger.warning("hCaptcha detected")
                return True, "hcaptcha"
            
            # Check for reCAPTCHA
            if "recaptcha" in page_source or "g-recaptcha" in page_source:
                logger.warning("reCAPTCHA detected")
                return True, "recaptcha"
            
            # Check for CAPTCHA images
            captcha_selectors = [
                'img[src*="captcha"]',
                'img[alt*="captcha"]',
                'img[title*="captcha"]',
                'div[id*="captcha"]',
                'div[class*="captcha"]',
                'input[name*="captcha"]'
            ]
            
            for selector in captcha_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.warning(f"CAPTCHA element found with selector: {selector}")
                        return True, "image_captcha"
                except:
                    continue
            
            # Check for "verify you are human" messages
            captcha_keywords = [
                "captcha",
                "verify you are human",
                "please verify",
                "security check",
                "human verification",
                "challenge page"
            ]
            
            for keyword in captcha_keywords:
                if keyword in page_source:
                    logger.warning(f"CAPTCHA keyword detected: {keyword}")
                    return True, "text_captcha"
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error checking for CAPTCHA: {e}")
            return False, None
    
    def _handle_captcha(self, captcha_type, context_info=""):
        """
        Handle CAPTCHA detection
        Returns: (bool, str) - (success, message)
        """
        self.captcha_detected = True
        self.captcha_url = self.driver.current_url
        self.captcha_retries += 1
        
        logger.warning(f"CAPTCHA detected (type: {captcha_type}) at {self.driver.current_url}")
        print("\n" + "="*60)
        print("⚠️ CAPTCHA DETECTED")
        print("="*60)
        print(f"Type: {captcha_type}")
        print(f"URL: {self.driver.current_url}")
        print(f"Context: {context_info}")
        print(f"Retry count: {self.captcha_retries}/{self.max_captcha_retries}")
        print("="*60)
        
        # Save screenshot for debugging
        try:
            timestamp = int(time.time())
            screenshot_path = f"captcha_detected_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved: {screenshot_path}")
        except Exception as e:
            print(f"Could not save screenshot: {e}")
        
        # Save page source for debugging
        try:
            timestamp = int(time.time())
            page_source_path = f"captcha_page_{timestamp}.html"
            with open(page_source_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            print(f"Page source saved: {page_source_path}")
        except Exception as e:
            print(f"Could not save page source: {e}")
        
        # Different handling based on CAPTCHA type
        if captcha_type == "hcaptcha":
            print("\n⚠️ hCaptcha detected")
            print("Manual solving required.")
            return False, "hcaptcha_detected"
        
        elif captcha_type == "recaptcha":
            print("\n⚠️ reCAPTCHA detected")
            print("Manual solving required.")
            return False, "recaptcha_detected"
        
        else:
            print("\n⚠️ Generic CAPTCHA detected")
            print("Manual solving may be required.")
            return False, "captcha_detected"
    
    def wait_for_element(self, by, value, timeout=30, check_captcha=True):
        """Wait for element to be present, checking for CAPTCHA"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            
            # Check for CAPTCHA after waiting
            if check_captcha:
                is_captcha, captcha_type = self._check_captcha()
                if is_captcha:
                    success, message = self._handle_captcha(captcha_type, f"While waiting for element: {value}")
                    if not success:
                        return None
            
            return element
        except TimeoutException:
            # Check if timeout was due to CAPTCHA
            if check_captcha:
                is_captcha, captcha_type = self._check_captcha()
                if is_captcha:
                    success, message = self._handle_captcha(captcha_type, f"Timeout waiting for element: {value}")
            
            logger.warning(f"Timeout waiting for element: {value}")
            return None
    
    def navigate_to_url(self, url: str, check_captcha=True):
        """Navigate to URL and handle Cloudflare/CAPTCHA challenges"""
        full_url = url if url.startswith('http') else f"{self.base_url}{url}"
        logger.info(f"Navigating to: {full_url}")
        
        try:
            self.driver.get(full_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Check for Cloudflare challenge
            page_source = self.driver.page_source
            
            if 'Checking your browser' in page_source or 'cf-browser-verification' in page_source:
                logger.warning("Cloudflare challenge detected")
                print("\n⚠️ Cloudflare challenge detected. Waiting for it to complete...")
                
                # Wait for challenge to complete
                for i in range(1, 61):
                    time.sleep(1)
                    current_source = self.driver.page_source
                    if 'Checking your browser' not in current_source:
                        logger.info(f"Cloudflare challenge completed after {i} seconds")
                        break
                    
                    if i % 5 == 0:
                        print(f"  Still waiting... ({i}/60 seconds)")
                
                # Take screenshot
                try:
                    self.driver.save_screenshot('cloudflare_complete.png')
                    logger.info("Saved screenshot after Cloudflare challenge")
                except:
                    pass
            
            # Check for CAPTCHA after navigation
            if check_captcha:
                is_captcha, captcha_type = self._check_captcha()
                if is_captcha:
                    success, message = self._handle_captcha(captcha_type, f"After navigating to: {full_url}")
                    if not success:
                        return False, message
            
            # Wait a bit more for content to load
            time.sleep(2)
            
            # Save page source for debugging
            try:
                with open('current_page.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source[:50000])
                logger.info("Saved page source to current_page.html")
            except:
                pass
            
            logger.info("Navigation successful")
            return True, "success"
            
        except Exception as e:
            logger.error(f"Failed to navigate to {full_url}: {e}")
            return False, str(e)
    
    def get_page_with_captcha_handling(self, url, max_retries=3):
        """Get page content with CAPTCHA handling and retries"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1}/{max_retries} to get {url}")
                
                # Navigate to URL
                success, message = self.navigate_to_url(url)
                
                if not success:
                    if "captcha" in message.lower():
                        logger.warning(f"CAPTCHA detected on attempt {attempt + 1}")
                        
                        if attempt < max_retries - 1:
                            logger.info(f"Retrying in 5 seconds...")
                            time.sleep(5)
                            continue
                        else:
                            logger.error(f"Max retries reached with CAPTCHA")
                            return None, "max_captcha_retries_reached"
                    else:
                        logger.error(f"Navigation failed: {message}")
                        return None, message
                
                # Get page content
                page_source = self.driver.page_source
                
                # Verify we got valid content (not a CAPTCHA page)
                is_captcha, captcha_type = self._check_captcha()
                if is_captcha:
                    logger.warning(f"CAPTCHA still present after navigation")
                    
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in 5 seconds...")
                        time.sleep(5)
                        continue
                    else:
                        logger.error(f"Max retries reached, CAPTCHA persists")
                        return None, "captcha_persists"
                
                return page_source, "success"
                
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}: {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
        
        return None, "max_attempts_exceeded"
    
    def solve_captcha_manually(self, wait_time=60):
        """
        Wait for user to solve CAPTCHA manually
        Returns: bool - True if CAPTCHA appears solved
        """
        print(f"\n⏳ Waiting {wait_time} seconds for manual CAPTCHA solving...")
        print(f"Please visit: {self.driver.current_url}")
        print("Solve the CAPTCHA in the browser window.")
        
        for i in range(wait_time):
            time.sleep(1)
            
            # Check if CAPTCHA is still present
            is_captcha, captcha_type = self._check_captcha()
            
            if not is_captcha:
                print(f"\n✅ CAPTCHA appears to be solved after {i+1} seconds")
                self.captcha_detected = False
                self.captcha_url = None
                return True
            
            if (i + 1) % 10 == 0:
                print(f"  {i+1}/{wait_time} seconds elapsed...")
        
        print(f"\n❌ Timeout waiting for CAPTCHA solving")
        return False
    
    def get_game_technologies(self, appid, game_name=""):
        """
        Get technologies for a game from the main app page
        Returns: (list, str, str) - (technologies_list, status_message, captcha_url_if_detected)
        """
        url = f"https://steamdb.info/app/{appid}/"  # NOT /technologies/
        
        try:
            logger.info(f"Fetching technologies for {game_name} (AppID: {appid})")
            
            # Get page with CAPTCHA handling
            page_source, status = self.get_page_with_captcha_handling(url, max_retries=2)
            
            if page_source is None:
                if "captcha" in status:
                    logger.warning(f"CAPTCHA detected for {game_name}")
                    return [], "captcha_detected", self.driver.current_url
                else:
                    return [], status, None
            
            # Parse technologies from the main app page
            technologies = []
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find the technologies row - looking for <td>Technologies</td>
            rows = soup.find_all('tr')
            for row in rows:
                th = row.find('th')
                if th and 'technologies' in th.get_text(strip=True).lower():
                    # Found the technologies row
                    td = row.find('td')
                    if td:
                        # Extract technology links
                        tech_links = td.find_all('a')
                        for link in tech_links:
                            tech_name = link.get_text(strip=True)
                            if tech_name:
                                technologies.append(tech_name)
                        
                        # If no links found, try getting text directly
                        if not technologies:
                            td_text = td.get_text(strip=True)
                            if td_text and td_text.lower() not in ['n/a', 'none', '']:
                                # Split by commas and clean up
                                tech_list = [t.strip() for t in td_text.split(',') if t.strip()]
                                technologies.extend(tech_list)
                    
                    break  # Found technologies, stop searching
            
            # Alternative search patterns if the above doesn't work
            if not technologies:
                # Look for any table cell containing technology info
                for td in soup.find_all('td'):
                    if td.find_parent('tr') and any(keyword in td.get_text().lower() 
                                                   for keyword in ['engine', 'sdk', 'anticheat', 'technology']):
                        links = td.find_all('a')
                        for link in links:
                            tech_name = link.get_text(strip=True)
                            if tech_name and len(tech_name) > 1:
                                technologies.append(tech_name)
            
            if technologies:
                logger.info(f"Found {len(technologies)} technologies for {game_name}")
                # Clean up technologies - remove duplicates and sort
                technologies = list(dict.fromkeys(technologies))
                technologies.sort()
                return technologies, "success", None
            else:
                logger.info(f"No technologies found for {game_name}")
                return [], "no_technologies_found", None
            
        except Exception as e:
            logger.error(f"Error getting technologies for {appid}: {e}")
            return [], str(e), None

    def setup_driver(self, max_retries: int = 3):
        """Setup Chrome driver with multiple fallback strategies and detailed logging"""
        logger.info("="*60)
        logger.info("STARTING CHROME DRIVER SETUP")
        logger.info("="*60)
        
        chrome_options = Options()
        
        # Add arguments to make Chrome look more like a real browser
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add user agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36')
        
        # Window size
        chrome_options.add_argument('--window-size=1920,1080')
        
        if self.headless:
            chrome_options.add_argument('--headless')
            logger.info("Running in HEADLESS mode")
        else:
            logger.info("Running in HEADED mode (visible browser)")
        
        # Disable dev shm usage
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        
        # Add language preference
        chrome_options.add_argument('--lang=en-US,en;q=0.9')
        
        # Strategy 1: Try webdriver-manager (auto-download ChromeDriver)
        logger.info("\n[Strategy 1] Trying webdriver-manager (auto-download)...")
        try:
            logger.info("  → Calling ChromeDriverManager().install()...")
            service = Service(ChromeDriverManager().install())
            logger.info("  → ChromeDriver path obtained, creating Chrome instance...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute CDP commands to avoid detection
            logger.info("  → Setting anti-detection scripts...")
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("  ✅ SUCCESS with webdriver-manager!")
            logger.info("="*60)
            return True
            
        except Exception as e:
            logger.error(f"  ❌ webdriver-manager failed: {type(e).__name__}: {str(e)[:200]}")
            if "Could not reach host" in str(e) or "offline" in str(e).lower():
                logger.error("  → Network error: Cannot download ChromeDriver from internet")
            logger.info("  → Falling back to next strategy...")
        
        # Strategy 2: Try system ChromeDriver (already installed)
        logger.info("\n[Strategy 2] Trying system ChromeDriver...")
        
        import shutil
        system_chromedriver = shutil.which('chromedriver')
        
        if system_chromedriver:
            logger.info(f"  → Found chromedriver at: {system_chromedriver}")
            try:
                service = Service(executable_path=system_chromedriver)
                logger.info("  → Creating Chrome instance with system chromedriver...")
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                
                # Execute CDP commands to avoid detection
                logger.info("  → Setting anti-detection scripts...")
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                logger.info("  ✅ SUCCESS with system ChromeDriver!")
                logger.info("="*60)
                return True
                
            except Exception as e:
                logger.error(f"  ❌ System ChromeDriver failed: {type(e).__name__}: {str(e)[:200]}")
                logger.info("  → Falling back to next strategy...")
        else:
            logger.warning("  ⚠️  System ChromeDriver not found in PATH")
            logger.info("  → Falling back to next strategy...")
        
        # Strategy 3: Try common ChromeDriver locations on Windows
        logger.info("\n[Strategy 3] Trying common Windows ChromeDriver locations...")
        
        common_paths = [
            r'C:\Program Files\Google\Chrome\Application\chromedriver.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe',
            r'C:\chromedriver.exe',
            r'C:\Windows\chromedriver.exe',
            r'.\chromedriver.exe',
            './chromedriver.exe'
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                logger.info(f"  → Found chromedriver at: {path}")
                try:
                    service = Service(executable_path=path)
                    logger.info("  → Creating Chrome instance...")
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    
                    # Execute CDP commands to avoid detection
                    logger.info("  → Setting anti-detection scripts...")
                    self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    
                    logger.info(f"  ✅ SUCCESS with ChromeDriver at {path}!")
                    logger.info("="*60)
                    return True
                    
                except Exception as e:
                    logger.error(f"  ❌ Failed with {path}: {type(e).__name__}: {str(e)[:200]}")
                    continue
        
        logger.warning("  ⚠️  No ChromeDriver found in common locations")
        
        # Strategy 4: Try without specifying service (let Selenium find it)
        logger.info("\n[Strategy 4] Trying default Selenium ChromeDriver detection...")
        try:
            logger.info("  → Creating Chrome instance with default settings...")
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Execute CDP commands to avoid detection
            logger.info("  → Setting anti-detection scripts...")
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("  ✅ SUCCESS with default Selenium detection!")
            logger.info("="*60)
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Default detection failed: {type(e).__name__}: {str(e)[:200]}")
        
        # All strategies failed
        logger.error("\n" + "="*60)
        logger.error("ALL CHROME DRIVER SETUP STRATEGIES FAILED")
        logger.error("="*60)
        logger.error("\nPossible solutions:")
        logger.error("1. Check internet connection (needed for webdriver-manager)")
        logger.error("2. Download ChromeDriver manually from: https://chromedriver.chromium.org/")
        logger.error("3. Place chromedriver.exe in one of these locations:")
        for path in common_paths[:5]:
            logger.error(f"   - {path}")
        logger.error("4. Add chromedriver.exe to your PATH environment variable")
        logger.error("5. Install Chrome browser if not already installed")
        logger.error("="*60)
        
        return False
    
    def setup_driver_with_turnstile(self, max_retries: int = 3) -> bool:
        """Setup driver (Turnstile solver removed)"""
        return self.setup_driver(max_retries)
    
    def check_for_captcha(self, page_source: str = None) -> Tuple[bool, str, str]:
        """
        Check if CAPTCHA is present and extract necessary information
        
        Returns:
            Tuple: (is_captcha_present, captcha_url, captcha_status_message)
        """
        try:
            if page_source is None:
                page_source = self.driver.page_source
            
            page_lower = page_source.lower()
            
            # Check for various CAPTCHA indicators
            captcha_indicators = [
                'cf-chl-widget',
                'data-sitekey',
                'challenges.cloudflare.com',
                'turnstile',
                'verify you are human',
                'cloudflare challenge',
                'just a moment'
            ]
            
            has_captcha = any(indicator in page_lower for indicator in captcha_indicators)
            
            if not has_captcha:
                return False, None, "No CAPTCHA detected"
            
            # Try to extract CAPTCHA URL for iframe
            captcha_url = None
            
            # Method 1: Look for iframe with Cloudflare challenge
            try:
                iframe = self.driver.find_element(By.CSS_SELECTOR, 'iframe[src*="challenges.cloudflare.com"]')
                captcha_url = iframe.get_attribute('src')
                logger.info(f"Found CAPTCHA iframe URL: {captcha_url}")
            except:
                # Method 2: Look for Turnstile widget
                try:
                    widget = self.driver.find_element(By.CSS_SELECTOR, 'div[data-sitekey]')
                    sitekey = widget.get_attribute('data-sitekey')
                    captcha_url = f"https://challenges.cloudflare.com/turnstile/v0/api/fallback?sitekey={sitekey}"
                    logger.info(f"Found Turnstile widget with sitekey: {sitekey}")
                except:
                    # Method 3: Generic Cloudflare challenge URL
                    captcha_url = "https://challenges.cloudflare.com/cdn-cgi/challenge-platform/h/g/turnstile/iframe/5/rcv.html"
            
            self.captcha_detected = True
            self.captcha_url = captcha_url
            self.captcha_status = "CAPTCHA detected - requires user interaction"
            
            logger.warning(f"CAPTCHA detected: {captcha_url}")
            return True, captcha_url, "CAPTCHA detected. Please solve to continue."
            
        except Exception as e:
            logger.error(f"Error checking for CAPTCHA: {e}")
            return False, None, f"Error checking CAPTCHA: {str(e)}"
    
    def navigate_to_url_with_captcha_handling(self, url: str) -> Tuple[bool, str]:
        """
        Navigate to URL with CAPTCHA detection
        
        Returns:
            Tuple: (success, message)
        """
        full_url = url if url.startswith('http') else f"{self.base_url}{url}"
        logger.info(f"Navigating to: {full_url}")
        
        try:
            self.driver.get(full_url)
            time.sleep(3)  # Wait for page load
            
            # Check for CAPTCHA
            has_captcha, captcha_url, message = self.check_for_captcha()
            
            if has_captcha:
                self.captcha_detected = True
                self.captcha_url = captcha_url
                return False, f"CAPTCHA detected at {full_url}. Please solve it to continue."
            
            return True, f"Successfully navigated to {full_url}"
            
        except Exception as e:
            error_msg = f"Failed to navigate to {full_url}: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def _extract_technologies_from_soup(self, soup: BeautifulSoup) -> List[str]:
        """Extract technologies from BeautifulSoup object"""
        technologies = []
        
        # Look for the technologies row specifically
        rows = soup.find_all('tr')
        for row in rows:
            th = row.find('th')
            if th and 'technologies' in th.get_text(strip=True).lower():
                td = row.find('td')
                if td:
                    # Extract all technology links
                    tech_links = td.find_all('a')
                    for link in tech_links:
                        tech_name = link.get_text(strip=True)
                        if tech_name:
                            technologies.append(tech_name)
                    
                    # If no links, try plain text
                    if not technologies:
                        td_text = td.get_text(strip=True)
                        if td_text and td_text.lower() not in ['n/a', 'none', '']:
                            tech_list = [t.strip() for t in td_text.split(',') if t.strip()]
                            technologies.extend(tech_list)
                break  # Found technologies, stop searching
        
        # Alternative: search for any technology mentions
        if not technologies:
            for elem in soup.find_all(['td', 'div', 'span']):
                text = elem.get_text(strip=True)
                if any(keyword in text.lower() for keyword in ['engine', 'sdk', 'framework', 'api']):
                    links = elem.find_all('a')
                    for link in links:
                        tech_name = link.get_text(strip=True)
                        if tech_name and len(tech_name) > 1:
                            technologies.append(tech_name)
        
        # Clean and deduplicate
        technologies = list(dict.fromkeys(tech for tech in technologies if tech))
        return technologies
    
    def navigate_to_url_with_turnstile(self, url: str, bypass_turnstile: bool = True, max_retries: int = 3) -> bool:
        """
        Navigate to URL (Turnstile solver removed)
        
        Args:
            url: URL to navigate to
            bypass_turnstile: Ignored (kept for compatibility)
            max_retries: Maximum retry attempts
            
        Returns:
            True if navigation successful, False otherwise
        """
        full_url = url if url.startswith('http') else f"{self.base_url}{url}"
        logger.info(f"Navigating to: {full_url}")
        
        for attempt in range(max_retries):
            try:
                self.driver.get(full_url)
                time.sleep(3)  # Wait for page load
                
                # Check if navigation successful
                if 'steamdb.info' in self.driver.current_url:
                    return True
                
            except Exception as e:
                logger.error(f"Navigation attempt {attempt+1} failed: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(2)
        
        logger.error(f"Failed to navigate to {full_url} after {max_retries} attempts")
        return False
    
    def remove_min_reviews_filter(self):
        """Remove the '≥ 500 reviews' filter from SteamDB page"""
        try:
            wait = WebDriverWait(self.driver, 5)
            
            # Check for active filters
            active_filters = self.driver.find_elements(By.CSS_SELECTOR, '.js-tag-active')
            if not active_filters:
                return
            
            # Find and remove '≥ 500 reviews'
            for filter_elem in active_filters:
                if '≥ 500 reviews' in filter_elem.text:
                    # Click the close button
                    close_btn = filter_elem.find_element(By.CSS_SELECTOR, '.js-tag-close')
                    close_btn.click()
                    time.sleep(0.5)
                    logger.info("Removed '≥ 500 reviews' filter")
                    break
                    
        except Exception as e:
            logger.warning(f"Error removing min reviews filter: {e}")
    
    def remove_all_filters_if_present(self):
        """Remove all active filters if present"""
        try:
            wait = WebDriverWait(self.driver, 5)
            
            # Find all active tags
            active_tags = self.driver.find_elements(By.CSS_SELECTOR, '.js-tag-active')
            for tag in active_tags:
                # Click close button
                close_btn = tag.find_element(By.CSS_SELECTOR, '.js-tag-close')
                close_btn.click()
                time.sleep(0.3)
            
            logger.info(f"Removed {len(active_tags)} active filters")
            
        except Exception as e:
            logger.warning(f"Error removing filters: {e}")
    
    def get_all_technologies(self) -> Dict:
        """Get all technology categories"""
        url = f"{self.base_url}/technologies/"
        
        if not self.navigate_to_url_with_turnstile(url, bypass_turnstile=True):
            return {}
        
        # Remove all filters if present
        self.remove_all_filters_if_present()
        
        # Wait for table to load
        time.sleep(2)
        
        categories = {}
        
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find all category sections
            category_sections = soup.find_all('h2', class_='table-heading')
            
            for section in category_sections:
                category_name = section.get_text(strip=True)
                category_table = section.find_next_sibling('table')
                
                if category_table:
                    techs = {}
                    
                    rows = category_table.find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            name_cell = cells[0]
                            count_cell = cells[1]
                            
                            link = name_cell.find('a')
                            if link:
                                tech_name = link.get_text(strip=True)
                                tech_link = link['href']
                                try:
                                    count = int(count_cell.get_text(strip=True).replace(',', ''))
                                except:
                                    count = 0
                                
                                techs[tech_name] = {
                                    'link': tech_link,
                                    'count': count
                                }
                    
                    if techs:
                        categories[category_name] = techs
            
            logger.info(f"Found {len(categories)} categories with total {sum(len(v) for v in categories.values())} technologies")
            
            # Save screenshot for debug
            self.driver.save_screenshot('tech_categories.png')
            
            return categories
            
        except Exception as e:
            logger.error(f"Failed to get technologies: {e}")
            with open('current_page.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            return {}
    
    def get_games_for_technology(self, tech_link: str, tech_name: str, 
                                max_pages: int = 3, count: int = 0) -> List[Dict]:
        """Get games for a specific technology"""
        if not self.navigate_to_url_with_turnstile(tech_link, bypass_turnstile=True):
            return []
        
        # Remove min reviews filter
        self.remove_min_reviews_filter()
        
        # Set to 'All' filter
        self._change_table_filter_to_all()
        
        games = []
        current_page = 1
        
        try:
            while current_page <= max_pages:
                # Parse current page
                current_games = self._parse_games_from_current_page()
                games.extend(current_games)
                
                if len(current_games) == 0:
                    break
                
                # Check for next page
                next_button = self.driver.find_elements(By.CSS_SELECTOR, '.paginate_container .next')
                if not next_button or 'disabled' in next_button[0].get_attribute('class'):
                    break
                
                # Click next
                next_button[0].click()
                time.sleep(2)
                
                current_page += 1
            
            logger.info(f"Found {len(games)} games for {tech_name}")
            return games
            
        except Exception as e:
            logger.error(f"Failed to get games for {tech_name}: {e}")
            return games
    
    def _change_table_filter_to_all(self):
        """Change table filter to 'All'"""
        try:
            select_elem = self.driver.find_element(By.CSS_SELECTOR, 'select.js-per-page')
            select = Select(select_elem)
            select.select_by_visible_text('All')
            time.sleep(1)
            logger.info("Set table filter to 'All'")
        except Exception as e:
            logger.warning(f"Failed to set 'All' filter: {e}")
    
    def _parse_games_from_current_page(self) -> List[Dict]:
        """Parse games from current table"""
        games = []
        
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            table = soup.find('table', class_='table')
            if table:
                rows = table.find_all('tr', class_='app')
                for row in rows:
                    try:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            appid_cell = cells[0]
                            name_cell = cells[1]
                            
                            appid = appid_cell.get_text(strip=True)
                            name = name_cell.get_text(strip=True)
                            
                            # Get links
                            steam_link = f"https://store.steampowered.com/app/{appid}/"
                            steamdb_link = f"{self.base_url}/app/{appid}/"
                            
                            games.append({
                                'appid': appid,
                                'name': name,
                                'steam_link': steam_link,
                                'steamdb_link': steamdb_link,
                                'image_link': f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{appid}/capsule_231x87.jpg",
                            })
                    except:
                        continue
            
            logger.info(f"Parsed {len(games)} games from current page")
            return games
            
        except Exception as e:
            logger.error(f"Error parsing page: {e}")
            return []
    
    def _extract_games_regex(self) -> List[Dict]:
        """Extract games directly from page source using regex"""
        games = []
        
        try:
            page_source = self.driver.page_source
            
            # Pattern to find app links with their text
            # This handles cases with mark tags: <a href="/app/368500/"><mark>Assassin</mark>'s <mark>Creed</mark>® <mark>Syndicate</mark></a>
            pattern = r'<a\s+href=["\']/app/(\d+)/["\'][^>]*>(.*?)</a>'
            
            matches = re.findall(pattern, page_source, re.IGNORECASE | re.DOTALL)
            
            for appid, html_content in matches:
                try:
                    # Extract text from HTML content (remove tags)
                    soup = BeautifulSoup(html_content, 'html.parser')
                    name = soup.get_text(strip=True)
                    
                    # Clean the name
                    name = re.sub(r'\s+', ' ', name).strip()
                    name = re.sub(r'[®©™]', '', name).strip()
                    
                    if name and len(name) > 2:
                        game_data = {
                            'appid': appid,
                            'name': name,
                            'steam_link': f"https://store.steampowered.com/app/{appid}/",
                            'steamdb_link': f"{self.base_url}/app/{appid}/",
                            'image_link': f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{appid}/capsule_231x87.jpg",
                        }
                        
                        # Check if this appid already exists
                        if not any(g['appid'] == appid for g in games):
                            games.append(game_data)
                            logger.debug(f"Regex extracted: {name} (AppID: {appid})")
                except:
                    continue
            
            logger.info(f"Regex extraction found {len(games)} games")
            
            return games
            
        except Exception as e:
            logger.error(f"Error in regex extraction: {e}")
            return games
    
    def search_steamdb_for_games(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search SteamDB for games"""
        search_url = f"{self.base_url}/search/?a=all&q={quote(query)}"
        
        logger.info(f"Searching SteamDB for: {query}")
        
        try:
            if not self.navigate_to_url_with_turnstile(search_url, bypass_turnstile=True):
                return []
            
            # Remove min reviews filter
            self.remove_min_reviews_filter()
            
            # Wait for search results
            time.sleep(3)
            
            # Parse results
            games = self._extract_games_regex()
            
            # Limit results
            games = games[:max_results]
            
            logger.info(f"Found {len(games)} games in SteamDB search for '{query}'")
            
            return games
            
        except Exception as e:
            logger.error(f"Failed to search SteamDB for '{query}': {e}")
            return []
    
    def search_steamdb_for_architecture(self, query: str) -> List[Dict]:
        """
        Search SteamDB for games using architecture query
        
        Args:
            query: Search query
        
        Returns:
            List of game dictionaries
        """
        search_url = f"{self.base_url}/search/?a=all&q={quote(query)}"
        
        logger.info(f"Searching SteamDB for architecture: {query}")
        
        try:
            if not self.navigate_to_url_with_turnstile(search_url, bypass_turnstile=True):
                return []
            
            # NEW: Remove min reviews filter
            self.remove_min_reviews_filter()
            
            # Wait for search results to load
            time.sleep(3)
            
            # For search, set to 'All' since results small
            self._change_table_filter_to_all()
            
            # Parse results
            games = self._parse_games_from_current_page()
            logger.info(f"Found {len(games)} games in SteamDB search for '{query}'")
            
            return games
            
        except Exception as e:
            logger.error(f"Failed to search SteamDB for '{query}': {e}")
            return []
    
    def find_psn_matches_for_steam_games(self, steam_games: List[Dict], 
                                        max_psn_results: int = 5) -> Dict[str, List[Dict]]:
        """
        Find PSN matches for Steam games
        
        Args:
            steam_games: List of Steam game dictionaries
            max_psn_results: Maximum PSN results per game
        
        Returns:
            Dictionary mapping Steam game names to PSN matches
        """
        matches = {}
        
        print(f"\n{'='*60}")
        print("SEARCHING FOR PSN MATCHES")
        print(f"{'='*60}")
        
        for i, steam_game in enumerate(steam_games):
            game_name = steam_game.get('name', '')
            appid = steam_game.get('appid', '')
            
            print(f"\n[{i+1}/{len(steam_games)}] Searching PSN for: {game_name}")
            
            # Search PSN for this game
            psn_results = self.psn_scraper.search_games(game_name, max_results=max_psn_results)
            
            if not psn_results:
                print(f"  No PSN results found for '{game_name}'")
                matches[game_name] = []
                continue
            
            print(f"  Found {len(psn_results)} PSN results")
            
            # Find the best match
            best_match, confidence = self.psn_scraper.find_matching_game(steam_game, psn_results)
            
            if best_match:
                print(f"  ✓ Best match: {best_match.name} (confidence: {confidence:.2f})")
                print(f"    PSN URL: {best_match.url}")
                print(f"    Price: {best_match.price}")
                print(f"    Type: {best_match.game_type}")
                if best_match.platform_tags:
                    print(f"    Platforms: {', '.join(best_match.platform_tags)}")
                
                # Get additional details for the best match
                if best_match.url:
                    details = self.psn_scraper.get_game_details(best_match.url)
                    if details:
                        best_match.description = details.get('description')
                        best_match.release_date = details.get('release_date')
                        best_match.developer = details.get('developer')
                        best_match.publisher = details.get('publisher')
                        best_match.rating = details.get('rating')
            else:
                print(f"  ✗ No good match found (best confidence: {confidence:.2f})")
                if psn_results:
                    print(f"    Closest matches:")
                    for j, psn_game in enumerate(psn_results[:3]):
                        print(f"      {j+1}. {psn_game.name} ({psn_game.game_type})")
            
            # Store all results
            game_matches = {
                'steam_game': steam_game,
                'psn_results': [game.to_dict() for game in psn_results],
                'best_match': best_match.to_dict() if best_match else None,
                'match_confidence': confidence
            }
            
            matches[game_name] = game_matches
            
            # Add delay to avoid rate limiting
            time.sleep(random.uniform(2, 4))
        
        print(f"\n{'='*60}")
        print("PSN MATCHING COMPLETE")
        print(f"{'='*60}")
        
        return matches
    
    def generate_json_output(self, categories: Dict, psn_matches: Dict = None, 
                           output_file: str = 'steamdb_psn_combined.json'):
        """Generate JSON output with both Steam and PSN data"""
        output_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'source': 'SteamDB + PSN Store',
                'steamdb_url': self.base_url,
                'psn_region': self.psn_scraper.region,
                'method': 'selenium_automation',
                'total_categories': len(categories),
                'total_technologies': sum(len(techs) for techs in categories.values()),
                'total_steam_games': sum(len(tech.get('games', [])) for category in categories.values() for tech in category.values()),
                'total_psn_matches': len(psn_matches) if psn_matches else 0
            },
            'technologies': categories,
            'psn_matches': psn_matches or {}
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Data saved to {output_file}")
        
        print("\n" + "="*60)
        print("PARSING SUMMARY")
        print("="*60)
        print(f"Output file: {output_file}")
        print(f"Total categories: {output_data['metadata']['total_categories']}")
        print(f"Total technologies: {output_data['metadata']['total_technologies']}")
        print(f"Total Steam games collected: {output_data['metadata']['total_steam_games']}")
        print(f"Total PSN matches analyzed: {output_data['metadata']['total_psn_matches']}")
        
        # Count successful PSN matches
        if psn_matches:
            successful_matches = sum(1 for match in psn_matches.values() if match.get('best_match'))
            print(f"Successful PSN matches: {successful_matches}")
        
        print("\nGames per technology:")
        for cat_name, techs in categories.items():
            for tech_name, tech_info in techs.items():
                if tech_info.get('games'):
                    print(f"  {cat_name}/{tech_name}: {len(tech_info['games'])} games")
        print("="*60)
        
        return output_data
    
    def test_psn_search(self, test_query: str = "bloons td 6"):
        """Test PSN search functionality"""
        print(f"\n{'='*60}")
        print("TESTING PSN SEARCH")
        print(f"{'='*60}")
        
        print(f"Searching for: '{test_query}'")
        results = self.psn_scraper.search_games(test_query, max_results=5)
        
        if not results:
            print("No results found!")
            return
        
        print(f"Found {len(results)} results:")
        for i, game in enumerate(results):
            print(f"\n{i+1}. {game.name}")
            print(f"   Title ID: {game.title_id}")
            print(f"   URL: {game.url}")
            print(f"   Price: {game.price}")
            print(f"   Type: {game.game_type}")
            if game.store_display_classification:
                print(f"   Classification: {game.store_display_classification}")
            if game.original_price:
                print(f"   Original: {game.original_price}")
            if game.discount_percent:
                print(f"   Discount: -{game.discount_percent}%")
            if game.platform_tags:
                print(f"   Platforms: {', '.join(game.platform_tags)}")
            if game.image_url:
                print(f"   Image: {game.image_url[:80]}...")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except:
                logger.warning("Error closing browser")

# Streamlit Integration Functions
def display_captcha_challenge(captcha_url: str, game_name: str = "", appid: str = ""):
    """
    Display CAPTCHA challenge in Streamlit with options
    
    Args:
        captcha_url: URL for CAPTCHA iframe
        game_name: Name of the game
        appid: Steam App ID
        
    Returns:
        str: User's choice ("continue", "skip", "retry")
    """
    import streamlit as st
    
    # Use appid to make keys unique
    key_prefix = f"captcha_{appid}" if appid else "captcha_global"
    
    st.markdown("### 🔒 CAPTCHA Challenge Detected")
    
    if game_name:
        st.warning(f"**{game_name}** (AppID: {appid}) requires CAPTCHA verification")
    else:
        st.warning("This page requires CAPTCHA verification")
    
    # Create columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Please solve the CAPTCHA below:**")
        
        # Display CAPTCHA iframe with styling
        captcha_html = f"""
        <div style="border: 2px solid #ff6b6b; padding: 15px; border-radius: 10px; margin: 10px 0; background: #1a1a1a;">
            <iframe src="{captcha_url}" 
                    width="100%" 
                    height="200" 
                    style="border: 1px solid #444; border-radius: 5px;"
                    allow="camera; microphone">
            </iframe>
            <p style="color: #888; font-size: 12px; margin-top: 10px; text-align: center;">
                If the CAPTCHA doesn't load, you may need to solve it directly in your browser.
            </p>
        </div>
        """
        st.components.v1.html(captcha_html, height=250)
    
    with col2:
        st.markdown("**Options:**")
        
        # Create buttons for different actions
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            if st.button("✅ I solved it", key=f"{key_prefix}_solved", use_container_width=True):
                st.success("Continuing...")
                return "continue"
        
        with col_btn2:
            if st.button("🔄 Retry", key=f"{key_prefix}_retry", use_container_width=True):
                st.info("Retrying...")
                return "retry"
        
        with col_btn3:
            if st.button("⏭️ Skip", key=f"{key_prefix}_skip", use_container_width=True):
                st.warning(f"Skipping {game_name if game_name else 'this game'}...")
                return "skip"
        
        # Additional help text
        st.markdown("---")
        st.markdown("**💡 Tips:**")
        st.markdown("""
        1. Solve the CAPTCHA above
        2. Click "I solved it"
        3. If stuck, try "Retry" or "Skip"
        """)
    
    return "waiting"

def display_technologies_results(technologies, game_name, appid):
    """Display technologies results"""
    st.success(f"✅ Found {len(technologies)} technologies for **{game_name}**")
    
    with st.expander(f"View Technologies for {game_name}"):
        for tech in technologies:
            st.markdown(f"- `{tech}`")
        
        st.markdown("---")
        st.markdown(f"**AppID:** `{appid}`")
        st.markdown(f"[🔗 View on SteamDB](https://steamdb.info/app/{appid}/)")  # Fixed URL

def display_no_technologies_message(message, game_name, appid):
    """Display message when no technologies found"""
    st.info(f"ℹ️ {message} for **{game_name}**")
    
    with st.expander(f"Details for {game_name}"):
        st.markdown(f"**Status:** {message}")
        st.markdown(f"**AppID:** `{appid}`")
        st.markdown(f"[🔗 View on SteamDB](https://steamdb.info/app/{appid}/)")  # Fixed URL

def run_technology_search_streamlit(parser, appid: str, game_name: str = ""):
    """
    Run technology search with Streamlit integration
    
    Args:
        parser: SteamDBSeleniumParser instance
        appid: Steam App ID
        game_name: Optional game name
        
    Returns:
        Tuple: (technologies_list, status, captcha_url_if_needed)
    """
    import streamlit as st
    
    # Create a placeholder for dynamic updates
    if f"tech_status_{appid}" not in st.session_state:
        st.session_state[f"tech_status_{appid}"] = st.empty()
    
    status_container = st.session_state[f"tech_status_{appid}"]
    
    with status_container.container():
        # Step 1: Show searching message
        st.info(f"🔍 Searching for technologies for **{game_name or f'AppID {appid}'}**...")
        
        # Step 2: Get technologies (this will detect CAPTCHA)
        technologies, message, captcha_url = parser.get_game_technologies(appid, game_name)
        
        # Step 3: Clear the status container and show results
        status_container.empty()
        
        if captcha_url:
            # CAPTCHA detected
            return [], "captcha", captcha_url
        elif technologies:
            # Technologies found
            return technologies, "success", None
        else:
            # No technologies found
            return [], message, None

def run_all_mode(args):
    """Run the 'all' command mode"""
    print("="*60)
    print("ALL MODE: Fetching all games and architectures")
    print("="*60)
    
    parser_obj = SteamDBSeleniumParser(headless=args.headless)
    
    print("\nSetting up Chrome browser...")
    if not parser_obj.setup_driver_with_turnstile():
        print("Failed to setup ChromeDriver. Exiting.")
        return
    
    print("\nFetching technology categories...")
    categories = parser_obj.get_all_technologies()
    
    if not categories:
        print("\nNo categories found. Check the screenshots and logs.")
        print("Check saved files: tech_categories.png, current_page.html")
        return
    
    target_categories = args.categories.split(',')
    categories = {k: v for k, v in categories.items() if k in target_categories}
    
    if not categories:
        print(f"\nNo matching categories found from: {target_categories}")
        print(f"Available categories: {list(categories.keys())}")
        return
    
    psn_matches = {}
    
    # Create SteamDB folder
    os.makedirs("SteamDB", exist_ok=True)
    
    if not args.test:
        print("\nFetching games for technologies...")
        for cat_name, techs in categories.items():
            print(f"\nProcessing {cat_name} category:")
            
            sorted_techs = sorted(
                techs.items(), 
                key=lambda x: x[1]['count'], 
                reverse=True
            )
            
            if args.limit_tech != -1:
                sorted_techs = sorted_techs[:args.limit_tech]
            
            for tech_name, tech_info in sorted_techs:
                if tech_info['count'] < args.min_count:
                    print(f"  Skipping {tech_name} (count: {tech_info['count']} < {args.min_count})")
                    continue
                
                print(f"  Fetching games for {tech_name} ({tech_info['count']} games total)...")
                try:
                    # Adjust max_pages based on count
                    if tech_info['count'] > 10000:
                        # For large counts, calculate pages needed (100 games per page)
                        games_per_page = 100
                        needed_pages = (tech_info['count'] // games_per_page) + 1
                        # Limit to reasonable number to avoid timeout
                        actual_max_pages = min(needed_pages, 100)  # Max 100 pages = 10k games
                        print(f"    Large dataset: using {actual_max_pages} pages")
                    else:
                        actual_max_pages = args.max_pages
                    
                    games = parser_obj.get_games_for_technology(
                        tech_info['link'],
                        tech_name,
                        max_pages=actual_max_pages,
                        count=tech_info['count']
                    )
                    
                    tech_info['games'] = games
                    print(f"    Found {len(games)} games (expected: {tech_info['count']})")
                    
                    # Calculate percentage retrieved
                    if tech_info['count'] > 0:
                        percentage = (len(games) / tech_info['count']) * 100
                        print(f"    Retrieved: {percentage:.1f}% of expected")
                    
                    tech_psn_matches = {}
                    if games and args.find_psn_matches:
                        print(f"    Searching for PSN matches...")
                        tech_psn_matches = parser_obj.find_psn_matches_for_steam_games(
                            games, 
                            max_psn_results=args.psn_max_results
                        )
                        psn_matches.update(tech_psn_matches)
                    
                    # Save individual JSON
                    file_name = f"{cat_name.lower()}_{tech_name.replace(' ', '_').replace('/', '_').replace('\\', '_')}.json"
                    file_path = os.path.join("SteamDB", file_name)
                    
                    tech_data = {
                        'metadata': {
                            'generated_at': datetime.now().isoformat(),
                            'category': cat_name,
                            'technology': tech_name,
                            'total_games': len(games),
                            'expected_games': tech_info['count'],
                            'retrieval_rate': f"{(len(games) / tech_info['count'] * 100) if tech_info['count'] > 0 else 0:.1f}%"
                        },
                        'technology_info': tech_info,
                        'games': games,
                        'psn_matches': tech_psn_matches
                    }
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(tech_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"    Saved results to {file_path}")
                    
                    # Add delay between technologies to avoid rate limiting
                    time.sleep(5)
                    
                except Exception as e:
                    print(f"    Error fetching games: {e}")
                    tech_info['games'] = []
                    tech_info['error'] = str(e)
    
    print(f"\nGenerating summary output: {args.output}")
    parser_obj.generate_json_output(categories, psn_matches, args.output)
    
    print("\n" + "="*60)
    print("PARSING COMPLETE!")
    print("="*60)
    print(f"Individual results saved to SteamDB folder")
    print(f"Summary output saved to: {args.output}")
    print(f"Log file: steamdb_psn_scraper.log")
    print(f"Debug files saved:")
    print(f"  - tech_categories.png (screenshot of categories page)")
    print(f"  - current_page.html (HTML of last page visited)")
    print(f"  - psn_search_debug.html (PSN search HTML)")
    print("="*60)
    
    parser_obj.close()


def run_query_mode(args):
    """Run the 'query' command mode"""
    print("="*60)
    print(f"QUERY MODE: Searching for game '{args.game_query}'")
    print("="*60)
    
    parser_obj = SteamDBSeleniumParser(headless=False)  # Non-headless for query mode
    
    print("\nSetting up Chrome browser...")
    if not parser_obj.setup_driver_with_turnstile():
        print("Failed to setup ChromeDriver. Exiting.")
        return
    
    # Step 1: Query PSN with pagination
    print(f"\nSearching PSN for '{args.game_query}'...")
    psn_results = parser_obj.psn_scraper.search_games_with_pagination(args.game_query, max_results=200)
    
    if not psn_results:
        print("No PSN results found.")
        parser_obj.close()
        return
    
    # Count game types
    game_type_counts = {}
    for game in psn_results:
        game_type = game.game_type
        game_type_counts[game_type] = game_type_counts.get(game_type, 0) + 1
    
    print(f"\n{'='*60}")
    print(f"FOUND {len(psn_results)} PSN RESULTS FOR '{args.game_query}'")
    print(f"Game Types: {', '.join([f'{k}: {v}' for k, v in game_type_counts.items()])}")
    print("="*60)
    
    # Show first 10 results
    for i, game in enumerate(psn_results[:10]):
        print(f"\n{i+1:3d}. {game.name}")
        print(f"     ID: {game.title_id}")
        print(f"     Price: {game.price}")
        print(f"     Type: {game.game_type}")
    
    if len(psn_results) > 10:
        print(f"\n... and {len(psn_results) - 10} more results")
    
    print("\n" + "="*60)
    print("PSN SEARCH COMPLETE")
    print(f"Total results: {len(psn_results)}")
    print(f"Full Games: {game_type_counts.get('Full Game', 0)}")
    print(f"Add-ons/DLC: {game_type_counts.get('Add-on', 0)}")
    print(f"Bundles: {game_type_counts.get('Bundle', 0)}")
    print(f"Other types: {sum(v for k, v in game_type_counts.items() if k not in ['Full Game', 'Add-on', 'Bundle'])}")
    print("="*60)
    
    # Ask user what to do next
    print(f"\nWhat would you like to do next?")
    print("  1. Search SteamDB for ALL PSN results")
    print("  2. Select specific PSN games to search")
    print("  3. Search SteamDB for Full Games only")
    print("  4. Exit without searching SteamDB")
    
    choice = input("\nEnter choice (1/2/3/4, default=1): ").strip() or "1"
    
    if choice == "4":
        print("Exiting without SteamDB search.")
        parser_obj.close()
        return
    
    selected_psn_games = []
    
    if choice == "1":
        # Search SteamDB for ALL PSN results
        selected_psn_games = psn_results
        print(f"\nSearching SteamDB for ALL {len(psn_results)} PSN results...")
    
    elif choice == "2":
        # Let user select specific games
        print("\nEnter the numbers of PSN games to search (comma-separated, e.g., 1,3,5):")
        print("Or enter 'all' to search all games.")
        print("Or enter 'full' to search only Full Games.")
        print("Or enter 'addons' to search only Add-ons.")
        selection = input("Numbers/command: ").strip().lower()
        
        if selection == 'all':
            selected_psn_games = psn_results
            print(f"Searching ALL {len(psn_results)} games...")
        elif selection == 'full':
            selected_psn_games = [game for game in psn_results if game.game_type == "Full Game"]
            print(f"Searching {len(selected_psn_games)} Full Games...")
        elif selection == 'addons':
            selected_psn_games = [game for game in psn_results if game.game_type == "Add-on"]
            print(f"Searching {len(selected_psn_games)} Add-ons/DLC...")
        elif selection:
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                selected_psn_games = [psn_results[i] for i in indices if 0 <= i < len(psn_results)]
                print(f"Selected {len(selected_psn_games)} games for SteamDB search.")
            except ValueError:
                print("Invalid input. Searching all games.")
                selected_psn_games = psn_results
        else:
            selected_psn_games = psn_results
    
    elif choice == "3":
        # Search only Full Games
        selected_psn_games = [game for game in psn_results if game.game_type == "Full Game"]
        print(f"\nSearching {len(selected_psn_games)} Full Games...")
    
    else:
        selected_psn_games = psn_results
        print("Searching first 10 games.")
    
    if not selected_psn_games:
        print("No games selected for SteamDB search.")
        parser_obj.close()
        return
    
    all_steam_results = []
    all_technologies = {}
    
    # Step 2: Search SteamDB for each selected PSN game
    print(f"\n{'='*60}")
    print(f"SEARCHING STEAMDB FOR {len(selected_psn_games)} GAMES")
    print("="*60)
    
    for idx, psn_game in enumerate(selected_psn_games):
        print(f"\n[{idx+1}/{len(selected_psn_games)}] Searching SteamDB for:")
        print(f"    PSN: {psn_game.name}")
        print(f"    ID: {psn_game.title_id}")
        print(f"    Type: {psn_game.game_type}")
        
        # Try multiple search strategies
        steam_games = []
        
        # Strategy 1: Direct search
        steam_games = parser_obj.search_steamdb_for_games(psn_game.name, max_results=15)
        
        # Strategy 2: If no results, try without "Assassin's Creed" prefix
        if not steam_games and "assassin's creed" in psn_game.name.lower():
            simpler_name = re.sub(r'assassin[\'\s]*creed[\s\:\-]*', '', psn_game.name, flags=re.IGNORECASE).strip()
            if simpler_name:
                print(f"    Trying simpler search: '{simpler_name}'")
                steam_games = parser_obj.search_steamdb_for_games(simpler_name, max_results=15)
        
        # Strategy 3: If still no results, try searching for just the subtitle
        if not steam_games:
            # Extract just the subtitle (after colon or dash)
            match = re.search(r'[:]\s*(.+)$', psn_game.name)
            if match:
                subtitle = match.group(1).strip()
                print(f"    Trying subtitle search: '{subtitle}'")
                steam_games = parser_obj.search_steamdb_for_games(subtitle, max_results=10)
        
        # Strategy 4: Try searching without special characters
        if not steam_games:
            clean_name = re.sub(r'[®©™]', '', psn_game.name).strip()
            if clean_name != psn_game.name:
                print(f"    Trying clean search: '{clean_name}'")
                steam_games = parser_obj.search_steamdb_for_games(clean_name, max_results=10)
        
        if not steam_games:
            print(f"    ✗ No SteamDB results found after multiple attempts.")
            logger.warning(f"No SteamDB results found for PSN game: {psn_game.name}")
            continue
        
        print(f"    ✓ Found {len(steam_games)} SteamDB results")
        
        # Show SteamDB results
        for i, game in enumerate(steam_games):
            print(f"      {i+1}. {game['name']} (AppID: {game['appid']})")
            if 'app_type' in game:
                print(f"         Type: {game['app_type']}")
            if 'release_date' in game:
                print(f"         Release: {game['release_date']}")
            if 'positive_percentage' in game:
                print(f"         Rating: {game['positive_percentage']}")
            
            logger.info(f"      SteamDB Result {i+1}: {game['name']} (AppID: {game['appid']})")
        
        # Collect all SteamDB results with PSN source info
        for steam_game in steam_games:
            steam_game['psn_source'] = {
                'name': psn_game.name,
                'title_id': psn_game.title_id,
                'url': psn_game.url,
                'price': psn_game.price,
                'platforms': psn_game.platform_tags,
                'game_type': psn_game.game_type,
                'store_display_classification': psn_game.store_display_classification
            }
            all_steam_results.append(steam_game)
        
        # Ask if user wants to get technologies for these SteamDB games
        if steam_games:
            print(f"\n    Get technologies for these {len(steam_games)} SteamDB games?")
            tech_choice = input("    (y/n, default=n): ").strip().lower()
            
            if tech_choice == 'y':
                selected_steam_games = steam_games
                
                if len(steam_games) > 1:
                    print(f"\n    Which games to get technologies for?")
                    print("    Enter 'all' or specific numbers (comma-separated):")
                    tech_selection = input("    Selection: ").strip().lower()
                    
                    if tech_selection != 'all':
                        try:
                            indices = [int(x.strip()) - 1 for x in tech_selection.split(',')]
                            selected_steam_games = [steam_games[i] for i in indices if 0 <= i < len(steam_games)]
                        except ValueError:
                            print("    Invalid input. Getting technologies for all games.")
                
                # Get technologies for selected Steam games
                for steam_idx, steam_game in enumerate(selected_steam_games):
                    print(f"\n      Getting technologies for:")
                    print(f"      Steam: {steam_game['name']} (AppID: {steam_game['appid']})")
                    
                    technologies = parser_obj.get_game_technologies(steam_game['appid'])
                    
                    if not technologies:
                        print("      No technologies/architectures found.")
                        steam_game['technologies'] = []
                    else:
                        print("      Technologies/Architectures:")
                        steam_game['technologies'] = technologies
                        for tech in technologies:
                            print(f"        - {tech}")
                        
                        # Store in technologies dict
                        all_technologies[steam_game['appid']] = technologies
                
                time.sleep(2)  # Small delay to avoid rate limiting
    
    # Save comprehensive output
    output_data = {
        'query': args.game_query,
        'timestamp': datetime.now().isoformat(),
        'psn_results': [g.to_dict() for g in psn_results],
        'steam_results': all_steam_results,
        'technologies': all_technologies,
        'summary': {
            'total_psn_results': len(psn_results),
            'total_steam_results': len(all_steam_results),
            'psn_games_searched': len(selected_psn_games),
            'steam_games_with_technologies': len(all_technologies),
            'game_type_counts': game_type_counts
        }
    }
    
    # Create a safe filename
    safe_query = re.sub(r'[^\w\s-]', '', args.game_query).strip().lower()
    safe_query = re.sub(r'[-\s]+', '_', safe_query)
    output_file = f"query_{safe_query}_results.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*60)
    print("QUERY COMPLETE!")
    print("="*60)
    print(f"Total PSN results found: {len(psn_results)}")
    print(f"Total SteamDB results found: {len(all_steam_results)}")
    print(f"Games with technologies: {len(all_technologies)}")
    print(f"Results saved to: {output_file}")
    print(f"Log file: steamdb_psn_scraper.log")
    print("="*60)
    
    # Show a quick summary
    if all_steam_results:
        print("\nQUICK SUMMARY:")
        print("-" * 40)
        unique_psn_games = set(r['psn_source']['name'] for r in all_steam_results)
        print(f"Unique PSN games matched: {len(unique_psn_games)}")
        
        # Count by game type
        game_type_matches = {}
        for r in all_steam_results:
            game_type = r['psn_source']['game_type']
            game_type_matches[game_type] = game_type_matches.get(game_type, 0) + 1
        
        for game_type, count in game_type_matches.items():
            print(f"  {game_type}: {count} matches")
    
    parser_obj.close()


# ===========================================
# PROSPERO PATCHES FUNCTIONALITY
# ===========================================

def search_prospero_patches(game_query: str, session: Optional[requests.Session] = None) -> Dict[str, Any]:
    """
    Search for PS5 game patches on prosperopatches.com
    Returns firmware information and patch history
    """
    if session is None:
        session = requests.Session()
    
    try:
        # Step 1: Search for the game
        search_url = "https://prosperopatches.com/api/internal/search"
        params = {"term": game_query}
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://prosperopatches.com/",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "fi-FI,fi;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        logger.info(f"Searching Prospero Patches for: {game_query}")
        response = session.get(search_url, params=params, headers=headers, timeout=15)
        
        if response.status_code != 200:
            logger.error(f"Search failed with status {response.status_code}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
        
        search_data = response.json()
        
        if not search_data.get("success") or not search_data.get("results"):
            logger.warning(f"No results found for: {game_query}")
            return {"success": False, "error": "No games found"}
        
        # Get all matching games
        games = search_data["results"]
        results = []
        
        for game in games:
            titleid = game.get("titleid")
            name = game.get("name")
            region = game.get("region")
            icon = game.get("icon")
            
            if not titleid:
                continue
            
            # Step 2: Load patches for this title
            logger.info(f"Loading patches for {name} ({titleid} - {region})")
            
            # Try to get the key from the page
            page_url = f"https://prosperopatches.com/{titleid}"
            page_headers = headers.copy()
            page_headers["accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
            page_headers["sec-fetch-mode"] = "navigate"
            page_headers["sec-fetch-dest"] = "document"
            page_headers["upgrade-insecure-requests"] = "1"
            
            page_response = session.get(page_url, headers=page_headers, timeout=15)
            
            # Extract key from page source - try multiple patterns
            key = None
            
            # Pattern 1: Look for the key in JavaScript variable assignment
            key_patterns = [
                r'var\s+key\s*=\s*["\']([a-f0-9]{64})["\']',
                r'"key"\s*:\s*"([a-f0-9]{64})"',
                r'key:\s*["\']([a-f0-9]{64})["\']',
                r'data-key=["\']([a-f0-9]{64})["\']',
                r'loadPatches\(["\']([a-f0-9]{64})["\']',
            ]
            
            for pattern in key_patterns:
                match = re.search(pattern, page_response.text)
                if match:
                    key = match.group(1)
                    logger.info(f"Found key for {titleid} using pattern: {pattern[:30]}...")
                    break
            
            if not key:
                # Try to find it in any script tag
                script_match = re.search(r'<script[^>]*>(.*?)</script>', page_response.text, re.DOTALL)
                if script_match:
                    script_content = script_match.group(1)
                    key_match = re.search(r'([a-f0-9]{64})', script_content)
                    if key_match:
                        key = key_match.group(1)
                        logger.info(f"Found potential key for {titleid} in script tag")
            
            if not key:
                logger.warning(f"Could not extract key for {titleid}")
                logger.debug(f"Page content sample: {page_response.text[:500]}")
                continue
            
            # Load patches - use proper POST format
            patch_url = "https://prosperopatches.com/api/internal/loadpatches"
            
            patch_headers = headers.copy()
            patch_headers["Content-Type"] = "application/json"  # Changed to application/json
            patch_headers["accept"] = "application/json"
            patch_headers["origin"] = "https://prosperopatches.com"
            patch_headers["referer"] = page_url
            patch_headers["sec-fetch-mode"] = "cors"
            
            # Send as JSON, not form data
            patch_payload = {
                "titleid": titleid,
                "key": key
            }
            
            logger.info(f"Requesting patches for {titleid} with key: {key[:16]}...")
            
            patch_response = session.post(
                patch_url, 
                json=patch_payload,  # Use json parameter instead of data
                headers=patch_headers,
                timeout=15
            )
            
            logger.info(f"Patch response status: {patch_response.status_code}")
            
            if patch_response.status_code == 200:
                try:
                    patch_info = patch_response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.debug(f"Response text: {patch_response.text[:200]}")
                    continue
                
                if patch_info.get("success"):
                    patches = patch_info.get("patches", [])
                    
                    # Find lowest firmware requirement
                    lowest_firmware = None
                    earliest_date = None
                    latest_version = None
                    
                    for patch in patches:
                        firmware = patch.get("required_firmware")
                        import_date = patch.get("import_date")
                        is_latest = patch.get("is_latest", False)
                        
                        if is_latest:
                            latest_version = patch.get("content_ver")
                        
                        if firmware:
                            if lowest_firmware is None or firmware < lowest_firmware:
                                lowest_firmware = firmware
                        
                        if import_date:
                            if earliest_date is None or import_date < earliest_date:
                                earliest_date = import_date
                    
                    results.append({
                        "titleid": titleid,
                        "name": name,
                        "region": region,
                        "icon": icon,
                        "patches": patches,
                        "patch_count": len(patches),
                        "lowest_firmware": lowest_firmware,
                        "earliest_import": earliest_date,
                        "latest_version": latest_version,
                        "last_updated": patch_info.get("lastupdated")
                    })
                    
                    logger.info(f"Successfully loaded {len(patches)} patches for {name}")
                else:
                    logger.warning(f"API returned success=false for {titleid}")
                    logger.debug(f"Response: {patch_info}")
            else:
                logger.warning(f"Failed to load patches for {titleid}: HTTP {patch_response.status_code}")
                logger.debug(f"Response: {patch_response.text[:200]}")
        
        return {
            "success": True,
            "query": game_query,
            "results": results,
            "total_games": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching Prospero Patches: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def search_orbis_patches(game_query: str, session: Optional[requests.Session] = None) -> Dict[str, Any]:
    """
    Search for PS4 game patches on orbispatches.com
    Uses the /api/internal/search endpoint and /api/internal/loadpatches POST endpoint.
    Title IDs are CUSA##### format.
    
    Returns firmware information and patch history for PS4 titles.
    """
    if session is None:
        session = requests.Session()

    base_url = "https://orbispatches.com"

    headers_common = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": f"{base_url}/",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "fi-FI,fi;q=0.9,en-US;q=0.8,en;q=0.7",
        "priority": "u=1, i"
    }

    try:
        # ── Step 1: Search for game by name OR direct CUSA lookup ──────────────
        is_titleid = bool(re.match(r'^CUSA\d{5,}$', game_query.strip().upper()))

        if is_titleid:
            # Direct title ID query: wrap as single-item result
            titleid = game_query.strip().upper()
            games = [{"titleid": titleid, "name": titleid, "region": None, "icon": None}]
            logger.info(f"Direct Title ID query: {titleid}")
        else:
            search_url = f"{base_url}/api/internal/search"
            params = {"term": game_query}

            logger.info(f"Searching ORBISPatches for: {game_query}")
            response = session.get(search_url, params=params, headers=headers_common, timeout=15)

            if response.status_code != 200:
                logger.error(f"Search failed with status {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}

            search_data = response.json()

            if not search_data.get("success") or not search_data.get("results"):
                return {"success": False, "error": "No PS4 games found"}

            games = search_data["results"]

        # ── Step 2: For each game, fetch page → extract key → load patches ────
        results = []

        for game in games:
            titleid = game.get("titleid")
            name = game.get("name", titleid)
            region = game.get("region")
            icon = game.get("icon")

            if not titleid:
                continue

            logger.info(f"Loading PS4 patches for {name} ({titleid} – {region})")

            # Fetch title page to get decryption key
            page_url = f"{base_url}/{titleid}"
            page_headers = headers_common.copy()
            page_headers.update({
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "sec-fetch-mode": "navigate",
                "sec-fetch-dest": "document",
                "upgrade-insecure-requests": "1",
                "priority": "u=0, i",
            })

            page_response = session.get(page_url, headers=page_headers, timeout=15)

            if page_response.status_code != 200:
                logger.warning(f"Could not load page for {titleid}: HTTP {page_response.status_code}")
                continue

            # Extract key – orbispatches embeds it in data-loadparams JSON attribute
            key = None
            page_text = page_response.text

            # Primary pattern: data-loadparams='{ "titleid": "CUSA...", "key": "hex64" }'
            key_patterns = [
                r'data-loadparams=["\'][^"\']*"key"\s*:\s*"([a-f0-9]{64})["\']',
                r'"key"\s*:\s*"([a-f0-9]{64})"',
                r"'key'\s*:\s*'([a-f0-9]{64})'",
                r'data-key=["\']([a-f0-9]{64})["\']',
                r'key:\s*["\']([a-f0-9]{64})["\']',
            ]

            for pattern in key_patterns:
                match = re.search(pattern, page_text)
                if match:
                    key = match.group(1)
                    logger.info(f"Found key for {titleid}")
                    break

            if not key:
                # Fallback: any 64-char hex string in the page
                hex_matches = re.findall(r'([a-f0-9]{64})', page_text)
                if hex_matches:
                    key = hex_matches[0]
                    logger.info(f"Used fallback hex key for {titleid}")

            # Also try to extract sidebar metadata from page HTML
            content_id = None
            publisher = None
            last_updated = None
            try:
                soup = BeautifulSoup(page_text, 'html.parser')
                # Sidebar info items
                for li in soup.select('li.bd-links-group'):
                    heading = li.find(class_='bd-links-heading')
                    if heading:
                        label = heading.get_text(strip=True).lower()
                        # Get the text that follows the heading within the <li>
                        full_text = li.get_text(strip=True)
                        value = full_text.replace(heading.get_text(strip=True), '', 1).strip()
                        # Strip any nested link text
                        value = re.sub(r'\s*View\s*', '', value).strip()
                        if 'content id' in label:
                            content_id = value
                        elif 'publisher' in label and 'id' not in label:
                            publisher = value
                # Last updated badge
                badge = soup.find('div', class_='bd-badge')
                if badge and 'last updated' in badge.get_text().lower():
                    last_updated = badge.get_text(strip=True).replace('Last updated', '').strip()
                # Icon from header bg
                if not icon:
                    img = soup.find('img', alt=name)
                    if img:
                        icon = img.get('src')
            except Exception as parse_err:
                logger.debug(f"Metadata parse error for {titleid}: {parse_err}")

            if not key:
                logger.warning(f"Could not extract key for {titleid}; skipping")
                continue

            # ── Step 3: POST to /api/internal/loadpatches ─────────────────────
            patch_url = f"{base_url}/api/internal/loadpatches"

            patch_headers = headers_common.copy()
            patch_headers.update({
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "accept": "application/json",
                "origin": base_url,
                "referer": page_url,
                "sec-fetch-mode": "no-cors",
            })

            # The API accepts JSON body (as seen in the reverse-engineered traffic)
            patch_payload_json = json.dumps({"titleid": titleid, "key": key})

            patch_response = session.post(
                patch_url,
                data=patch_payload_json,
                headers={**patch_headers, "Content-Type": "application/json"},
                timeout=15
            )

            logger.info(f"Orbis patch response status: {patch_response.status_code}")

            if patch_response.status_code != 200:
                logger.warning(f"Patch load failed for {titleid}: HTTP {patch_response.status_code}")
                continue

            try:
                patch_info = patch_response.json()
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse failed for {titleid}: {e}")
                continue

            if not patch_info.get("success"):
                logger.warning(f"API returned success=false for {titleid}")
                continue

            patches_raw = patch_info.get("patches", [])

            # Normalise patch fields (orbis uses version/filesize/required_firmware/creation_date)
            patches = []
            lowest_firmware = None
            latest_version = None

            for idx, p in enumerate(patches_raw):
                is_latest = p.get("is_latest", idx == 0)
                firmware = p.get("required_firmware")
                version = p.get("version") or p.get("content_ver", "N/A")

                if is_latest:
                    latest_version = version

                if firmware:
                    if lowest_firmware is None or firmware < lowest_firmware:
                        lowest_firmware = firmware

                patches.append({
                    "is_latest": is_latest,
                    "version": version,
                    "content_ver": version,
                    "filesize": p.get("filesize", "N/A"),
                    "required_firmware": firmware or "N/A",
                    "creation_date": p.get("creation_date", "N/A"),
                    "import_date": p.get("creation_date", "N/A"),
                    "changelog_preview": p.get("changelog_preview", ""),
                    "changelog_charcount": p.get("changelog_charcount", 0),
                    "keyset": p.get("keyset"),
                })

            results.append({
                "titleid": titleid,
                "name": patch_info.get("name", name),
                "region": region or "N/A",
                "icon": icon,
                "content_id": content_id,
                "publisher": publisher,
                "patches": patches,
                "patch_count": len(patches),
                "lowest_firmware": lowest_firmware,
                "latest_version": latest_version,
                "last_updated": last_updated,
            })

            logger.info(f"Loaded {len(patches)} PS4 patches for {name}")

        return {
            "success": True,
            "query": game_query,
            "results": results,
            "total_games": len(results)
        }

    except Exception as e:
        logger.error(f"Error searching ORBISPatches: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Parse SteamDB and find PSN matches')
    
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # 'all' subcommand
    parser_all = subparsers.add_parser('all', help='Get all games and architectures')
    parser_all.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser_all.add_argument('--min-count', type=int, default=1000, help='Minimum game count for technology')
    parser_all.add_argument('--max-pages', type=int, default=9999, help='Max pages per technology (high for all)')
    parser_all.add_argument('--output', type=str, default='steamdb_psn_combined.json', help='Output file')
    parser_all.add_argument('--test', action='store_true', help='Test mode - only fetch categories')
    parser_all.add_argument('--categories', type=str, default='Engine,SDK,Container,Emulator,Launcher,AntiCheat', help='Categories to scrape (comma-separated)')
    parser_all.add_argument('--limit-tech', type=int, default=-1, help='Limit number of technologies per category (-1 for all)')
    parser_all.add_argument('--psn-max-results', type=int, default=5, help='Max PSN results per game')
    parser_all.add_argument('--find-psn-matches', action='store_true', help='Find PSN matches for Steam games')
    
    # 'query' subcommand
    parser_query = subparsers.add_parser('query', help='Query for a specific game')
    parser_query.add_argument('game_query', type=str, help='Game name to query')
    
    # 'prospero' subcommand
    parser_prospero = subparsers.add_parser('prospero', help='Search Prospero Patches')
    parser_prospero.add_argument('game_query', type=str, help='Game name to query')
    
    args = parser.parse_args()
    
    if args.command == 'all':
        run_all_mode(args)
    elif args.command == 'query':
        run_query_mode(args)
    elif args.command == 'prospero':
        result = search_prospero_patches(args.game_query)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()