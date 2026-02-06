import argparse
import asyncio
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force unbuffered
sys.stdout.reconfigure(encoding='utf-8')

from scraper.pipeline import ScraperPipeline

async def main(country, trend_type, interests, ages, genders):
    print(f"--- PIPELINE RUNNER STARTED ({country}, {trend_type}) ---")
    if interests: print(f"Interests: {interests}")
    
    pipeline = ScraperPipeline()
    try:
        await pipeline.run(
            country=country, 
            trend_type=trend_type,
            interests=interests,
            ages=ages,
            genders=genders
        )
        print("--- PIPELINE RUNNER COMPLETED ---")
    except Exception as e:
        print(f"--- PIPELINE RUNNER FAILED: {e} ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--country", default="US")
    parser.add_argument("--type", default="growing")
    # Receive lists as comma-separated strings to handle spaces safely
    parser.add_argument("--interests", default="") # e.g. "Art,Home Decor"
    parser.add_argument("--ages", default="")
    parser.add_argument("--genders", default="")
    
    args = parser.parse_args()
    
    # Parse lists
    interests_list = [x.strip() for x in args.interests.split(",")] if args.interests else None
    ages_list = [x.strip() for x in args.ages.split(",")] if args.ages else None
    genders_list = [x.strip() for x in args.genders.split(",")] if args.genders else None
    
    asyncio.run(main(args.country, args.type, interests_list, ages_list, genders_list))
