import asyncio
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.pipeline import ScraperPipeline

async def main():
    print("Initializing Pinterest Trends Pipeline...")
    pipeline = ScraperPipeline()
    await pipeline.run()
    print("Pipeline completed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPipeline stopped by user.")
    except Exception as e:
        print(f"Pipeline error: {e}")
