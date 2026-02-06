from bs4 import BeautifulSoup
from typing import List, Dict, Optional

class PinterestParser:
    def parse_search_results(self, html_content: str) -> Dict:
        """Parses the search result page HTML."""
        soup = BeautifulSoup(html_content, "html.parser")
        
        pins = self._extract_pins(soup)
        related_keywords = self._extract_related_keywords(soup)
        
        return {
            "pins": pins,
            "related_keywords": related_keywords
        }

    def _extract_pins(self, soup: BeautifulSoup) -> List[Dict]:
        """Extracts pin metadata from the grid."""
        pins = []
        # Pinterest class names change frequently. 
        # We'll use more generic selectors or look for aria-labels/data-attributes where possible,
        # but realistically we often need to inspect the specific class names of the day.
        # For this MVP, we will try to find the pin wrapper.
        # Often pins are in 'div[data-test-id="pin-visual-wrapper"]' or similar.
        
        # NOTE: This selector is a best-guess and will likely need adjustment based on current Pinterest DOM.
        # We look for links that look like pins.
        
        pin_items = soup.find_all("div", {"data-test-id": "pin"})
        
        for item in pin_items:
            try:
                # Extract URL
                link_tag = item.find("a", href=True)
                if not link_tag:
                    continue
                pin_url = "https://www.pinterest.com" + link_tag['href']
                
                # Extract Title/Description (often in an alt tag of an image)
                img_tag = item.find("img")
                title = img_tag.get('alt', '') if img_tag else "No Title"
                
                # Extract Saves (This is tricky, often hidden or dynamically loaded, requires specific selectors)
                # Sometimes raw text inside the pin wrapper contains something like "1.2k"
                # We'll try to find a text node that looks like a number? 
                # For now, we might leave saves as 0 and refine later if not obvious.
                saves = 0 # Placeholder implementation
                
                pins.append({
                    "url": pin_url,
                    "title": title,
                    "saves": saves
                })
            except Exception as e:
                # Silently fail for individual malformed pins
                continue
                
        return pins

    def _extract_related_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extracts related search terms from the top chips."""
        related = []
        # Usually these are in a scrollable bar at the top, sometimes with data-test-id="bubble" or similar
        # Or look for 'div[role="button"]' with text.
        
        # Best guess:
        chips = soup.find_all("div", {"data-test-id": "bubble"})
        for chip in chips:
            text = chip.get_text(strip=True)
            if text:
                related.append(text)
                
        return requests_unique(related)

def requests_unique(l):
    return list(set(l))
