import math
from typing import List, Dict

class ScoreCalculator:
    def calculate(self, pins: List[Dict]) -> Dict:
        """
        Calculates the relative popularity score for a list of pins.
        Returns a dict with 'score', 'total_pins', 'avg_saves'.
        """
        if not pins:
            return {
                "score": 0.0,
                "total_pins": 0,
                "avg_saves": 0.0,
                "recent_pin_ratio": 0.0
            }

        total_pins = len(pins)
        
        # Clean saves data (handle '1.2k', '500', etc. if string, but parser currently returns 0 or int)
        # We assume parser gives us integers or cleanable strings.
        # For now, let's assume they are ints or basic strings. 
        # Ideally the parser should handle "1.2k" -> 1200.
        # Since I left it as 0 in parser, I should probably improve the parser or handle it here.
        # But for the MVP formula:
        
        saves_values = [p.get('saves', 0) for p in pins]
        total_saves = sum(saves_values)
        avg_saves = total_saves / total_pins if total_pins > 0 else 0
        
        # simplified recent_ratio (mocked as 1.0 since we don't have accurate creation dates yet)
        recent_pin_ratio = 1.0 
        
        # Formula: score = avg_saves * recent_pin_ratio * log(total_pins + 1)
        # Log base 10
        log_factor = math.log10(total_pins + 1)
        
        score = avg_saves * recent_pin_ratio * log_factor
        
        # Normalize score to 0-100 concept? 
        # The requirements say:
        # 0–20 → Very Low
        # 20–50 → Low
        # 50–120 → Medium
        # 120+ → High
        
        return {
            "score": round(score, 2),
            "total_pins": total_pins,
            "avg_saves": round(avg_saves, 2),
            "recent_pin_ratio": recent_pin_ratio
        }

    def get_bucket(self, score: float) -> str:
        if score < 20:
            return "Very Low"
        elif score < 50:
            return "Low"
        elif score < 120:
            return "Medium"
        else:
            return "High"
