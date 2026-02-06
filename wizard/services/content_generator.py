import os
import json
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

# Load env from root
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class ContentGeneratorService:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-lite-preview-02-05:free")
        
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
        Combines trend + suggestions for SEO.
        """
        if not trend: return []
        
        seo_keywords = set()
        seo_keywords.add(trend.lower())
        
        # Simple combinator logic (Trend + Suggestion)
        for sug in suggestions:
            if not sug: continue
            seo_keywords.add(f"{sug} {trend}".lower())
            if sug.lower() not in trend.lower():
                seo_keywords.add(f"{trend} {sug}".lower())
        
        return sorted(list(seo_keywords))

    def generate_titles(self, keyword: str, count: int = 5) -> List[str]:
        if not self.client:
            return [f"Mock Title for {keyword} (No API Key)"]
            
        try:
            prompt = (
                f"Generate {count} viral, high-CTR Pinterest pin titles for keyword '{keyword}'. "
                "Return ONLY titles, one per line."
            )
            
            completion = self.client.chat.completions.create(
                extra_headers={"X-Title": "PinTrends Wizard"},
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = completion.choices[0].message.content.strip()
            # Clean list
            titles = []
            for line in content.split('\n'):
                t = line.strip().lstrip('-').lstrip('1234567890.').strip()
                if t: titles.append(t)
            return titles[:count]
            
        except Exception as e:
            print(f"AI Title Error: {e}")
            return [f"Error Generating Titles: {e}"]

    def generate_description(self, keyword: str, title: str) -> str:
        if not self.client:
            return f"Mock description for {title}."
            
        try:
            prompt = (
                f"Write a 50-word SEO description for pin '{title}' (Keyword: {keyword}). "
                "Include hashtags."
            )
            
            completion = self.client.chat.completions.create(
                extra_headers={"X-Title": "PinTrends Wizard"},
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            return f"Error Generating Description: {e}"

    def generate_article_titles(self, keyword: str, count: int = 10) -> list:
        """
        Generates listicle article titles based on the user's specific SEO Strategist prompt.
        """
        if not self.client:
            return [{'title': f"{i} Ways to Rock {keyword}", 'hook': "Viral Hook"} for i in range(1, count+1)]
            
        prompt = f"""# Role
Act as a Senior SEO Strategist and Content Creator specializing in Gen-Z search trends and viral content.

# Task
Generate a list of {count} high-converting listicle article titles based on the primary keyword provided below.

# Input Data
**Primary Keyword:** "{keyword}"

# Process & Web Browsing
1. **Competitor Analysis:** Search the web for the top 5 ranking articles for this keyword. Analyze their titles for patterns, gaps, and emotional hooks.
2. **differentiation:** Create titles that stand out from these competitors (e.g., if they all use "Top 10," you use "7 Essential" or "The Ultimate List").

# Title Requirements (SEO & Style Guidelines)
1. **Keyword Placement:** naturally place the main keyword as close to the beginning of the title as possible (Front-loading).
2. **Length:** Keep titles between 50-60 characters to prevent truncation in SERPs (Search Engine Results Pages).
3. **Tone (Gen-Z Style):**
    - Use casual, authentic, and snappy language.
    - Avoid "corporate" or overly formal phrasing.
    - Focus on "vibes," "hacks," "truth," or "aesthetic."
    - Avoid "cringe" clickbait; keep it honest but catchy.
4. **Formatting:**
    - Use numbers (odd numbers like 7, 9, 13 often perform better).
    - Use brackets or parentheses for context (e.g., [2024 Guide], (Tried & Tested)).
5. **SEO Hygiene:** Do not over-optimize or "keyword stuff." The title must read naturally to a human.

# Output Format
Return ONLY a JSON array of objects with these keys: "title", "hook" (brief explanation or hook).
Example: [{{"title": "...", "hook": "..."}}]
"""
        try:
            completion = self.client.chat.completions.create(
                extra_headers={"X-Title": "PinTrends Wizard"},
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            content = self._clean_json(completion.choices[0].message.content)
            return json.loads(content)
        except Exception as e:
            print(f"Article Gen Error: {e}")
            return []

    def generate_pin_ideas(self, keyword: str, article_title: str, suggestions: list, count: int = 10) -> list:
        """
        Generates Pin titles and descriptions based on the user's specific Pinterest Strategist prompt.
        """
        if not self.client:
            return [{'title': f"Pin {i} for {keyword}", 'description': f"Desc {i} for {keyword}"} for i in range(1, count+1)]
            
        suggestions_text = ", ".join(suggestions)
        
        prompt = f"""## **Role**
Act as a professional Pinterest content strategist with deep expertise in Pinterest SEO, pin copywriting, and visual content marketing.

---
## **Context**
I have published a blog article with the following details:
- **Main Keyword:** {keyword}
- **Article Title:** {article_title}

I need you to create **{count} Pinterest listicle pin titles and descriptions** to drive traffic from Pinterest to this article.

---
## **Annotation & Secondary Keyword Bank**
Naturally weave in the following words and phrases where contextually relevant. Do not force every word into every pin. Use them strategically across all {count} pins for keyword diversity:
>{suggestions_text}

---
## **Requirements**

### Titles
1. Must be Pinterest SEO optimized and contain the main keyword or a close variation.
2. Must follow a listicle or power-word format that is visually appealing and click-worthy.
3. Keep titles concise, punchy, and scroll-stopping.

### Descriptions
1. **Every single description** must include the exact main keyword: **{keyword}**.
2. Naturally incorporate relevant secondary keywords and annotations from the bank above, varying them across descriptions.
3. Writing tone must feel **modern, fun, and relatable**, as if written by a trend-savvy 18-year-old who knows fashion.
4. Descriptions must be **engaging, conversational, and scroll-stopping** while remaining SEO-friendly and informative.
5. End every description with a **clear, strong call to action** (e.g., "Read the full list," "Tap to see all 17 outfits," "Save this for date night," etc.). Vary the CTAs across pins.
6. End each description with **3 to 5 relevant hashtags** related to the main keyword and Pinterest trending topics. Hashtags should feel natural, not spammy.

### Strict Rules
- **Do NOT** use emojis anywhere.
- **Do NOT** use dashes (hyphens or em dashes) anywhere.
- **Do NOT** include filler, fluff, or generic statements that add no value.
- **Do NOT** clone or repeat the same sentence structures across descriptions. Each one must feel unique.
- Every description must be **substantive and distinct** from the others.

---
## **Output Format**
Return ONLY a JSON array of objects with these keys: "title", "description".
Example: [{{"title": "...", "description": "..."}}]
"""
        try:
            completion = self.client.chat.completions.create(
                extra_headers={"X-Title": "PinTrends Wizard"},
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            content = self._clean_json(completion.choices[0].message.content)
            return json.loads(content)
        except Exception as e:
            print(f"Pin Gen Error: {e}")
            return []

    def _clean_json(self, content):
        import json
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return content.strip()

    def expand_keywords_with_ai(self, items: list, niche: str = "") -> list:
        """
        Use LLM to intelligently combine base keywords with suggestions.
        Input `items` should be a list of dicts: [{'keyword': 'base_kw', 'suggestions': ['s1', 's2']}]
        Analyzes each base keyword separately but in a single batch prompt if possible.
        """
        if not self.client:
            # Fallback
            results = []
            for item in items:
                base = item['keyword']
                sugs = item.get('suggestions', [])
                results.append({'keyword': base, 'base': base, 'intent': 'informational', 'score': 80})
                for s in sugs[:5]:
                     results.append({
                        'keyword': f"{base} {s}".lower(),
                        'base': base,
                        'intent': 'ideas',
                        'score': 70
                    })
            return results
        
        try:
            # Construct a structured prompt
            prompt_parts = [
                f"You are a Pinterest SEO expert. I have {len(items)} distinct topic groups. For EACH group, generate 5-8 specific long-tail search phrases that users search for on Pinterest.",
                f"NICHE: {niche or 'general'}",
                "\n--- GROUPS ---"
            ]
            
            for i, item in enumerate(items):
                kw = item['keyword']
                sugs = ", ".join(item.get('suggestions', [])[:20]) # Limit context per kw
                prompt_parts.append(f"GROUP {i+1}: Main Keyword: '{kw}' | Suggestions: {sugs}")
                
            prompt_parts.append("\nRULES:")
            prompt_parts.append("1. Generate phrases SPECIFIC to each group's main keyword. Do not mix topics.")
            prompt_parts.append("2. Use the provided suggestions to create natural long-tail variations.")
            prompt_parts.append("3. Keep phrases 2-6 words long.")
            prompt_parts.append("4. Assign a 'score' (0-100) based on search potential.")
            
            prompt_parts.append("\nReturn as a SINGLE JSON array containing all generated phrases, with the 'base' field indicating which main keyword it belongs to:")
            prompt_parts.append("""[{"keyword": "generated phrase", "base": "original main keyword", "score": 90}]""")
            prompt_parts.append("Return ONLY the JSON array.")

            prompt = "\n".join(prompt_parts)

            completion = self.client.chat.completions.create(
                extra_headers={"X-Title": "PinTrends Wizard"},
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = completion.choices[0].message.content.strip()
            
            import json
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            expanded = json.loads(content)
            
            # Fallback validation to ensure 'base' is present, though prompt asks for it
            # If missing, we might assume order? But prompt is explicit. 
            # We'll just pass it through.
                
            return expanded
            
        except Exception as e:
            print(f"AI Keyword Expansion Error: {e}")
            # Fallback
            results = []
            for item in items:
                base = item['keyword']
                results.append({'keyword': base, 'base': base, 'intent': 'informational', 'score': 80})
            return results

