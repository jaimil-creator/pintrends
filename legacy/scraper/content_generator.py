import os
from typing import List
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class ContentGenerator:
    def __init__(self):
        """
        Initialize the ContentGenerator with OpenRouter config.
        """
        # Debug: Print loaded key status (masked)
        key = os.getenv("OPENROUTER_API_KEY")
        # print(f"DEBUG: Env Load Path: {env_path}, Key Found: {bool(key)}")
        
        self.api_key = key or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.getenv("OPENROUTER_MODEL", "google/gemini-3-flash-preview")
        
        self.client = None
        if self.api_key:
            try:
                self.client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key,
                )
            except Exception as e:
                print(f"Failed to initialize OpenAI client: {e}")

    def generate_seo_keywords(self, trend: str, suggestions: List[str]) -> List[str]:
        """
        Combines the main trend with suggestions to create SEO-rich long-tail keywords.
        """
        if not trend:
            return []
            
        seo_keywords = set()
        # Add the trend itself
        seo_keywords.add(trend.lower())
        
        # Clean suggestions
        clean_suggestions = [s.strip() for s in suggestions if s and s.strip()]
        
        for sug in clean_suggestions:
            # Pattern 1: {Suggestion} {Trend}
            seo_keywords.add(f"{sug} {trend}".lower())
            
            # Pattern 2: {Trend} {Suggestion}
            # Only if suggestion isn't already part of trend (simple check)
            if sug.lower() not in trend.lower():
                seo_keywords.add(f"{trend} {sug}".lower())
                
        return sorted(list(seo_keywords))

    def generate_titles(self, keyword: str, count: int = 5) -> List[str]:
        """
        Generates high-CTR Pin titles using AI.
        """
        if not self.client:
            return [
                "API Key Missing: Set OPENROUTER_API_KEY in .env",
                f"10 Best {keyword.title()} Ideas",
                f"How to Style {keyword.title()}",
                f"The Ultimate {keyword.title()} Guide",
                f"{keyword.title()} Aesthetic 2026"
            ]
            
        try:
            prompt = (
                f"Generate {count} viral, high-CTR Pinterest pin titles for the keyword '{keyword}'. "
                "Keep them short, catchy, and emotional. "
                "Return ONLY the titles, one per line. Do not number them."
            )
            
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://pintrends.local", # Optional OpenRouter headers
                    "X-Title": "PinTrends App",
                },
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            content = completion.choices[0].message.content.strip()
            # Split by newlines and clean up numbering if AI adds it (1. Title -> Title)
            titles = []
            for line in content.split('\n'):
                clean_line = line.strip()
                # Remove leading numbers/bullets (e.g. "1. ", "- ")
                if clean_line:
                    import re
                    clean_line = re.sub(r'^[\d\-\.\s]+', '', clean_line)
                    titles.append(clean_line)
                    
            return titles[:count]
            
        except Exception as e:
            print(f"Error generating titles: {e}")
            return [
                f"Error: {str(e)}",
                f"Fallback: Top {keyword.title()} Ideas",
                f"Fallback: {keyword.title()} Inspo"
            ]

    def generate_descriptions(self, keyword: str, title: str) -> str:
        """
        Generates an SEO-optimized Pin description.
        """
        if not self.client:
            return f"Discover amazing ideas for {keyword}. #pinterest #{keyword.replace(' ', '')}"
            
        try:
            prompt = (
                f"Write a comprehensive, SEO-optimized Pinterest description (max 50 words) "
                f"for a pin titled '{title}'. "
                f"The main keyword is '{keyword}'. "
                "Include 3-5 relevant hashtags at the end. "
                "Make it engaging and actionable."
            )
            
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://pintrends.local",
                    "X-Title": "PinTrends App",
                },
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating description: {e}")
            return f"Check out this idea for {keyword}! #{keyword.replace(' ', '')}"

if __name__ == "__main__":
    # Test
    gen = ContentGenerator()
    print("Testing SEO Keywords...")
    print(gen.generate_seo_keywords("nails", ["red", "cute", "acrylic"]))
    
    print("\nTesting Title Generation (API)...")
    titles = gen.generate_titles("red nails")
    for t in titles:
        print(f"- {t}")
