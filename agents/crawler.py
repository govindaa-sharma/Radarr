import asyncio
import logfire
import yaml
from pathlib import Path
from tools.scraper import scrape_url
from agents.analyst import analyse_url
from config.observability import configure_observability
from dotenv import load_dotenv

load_dotenv()
configure_observability()

def load_competitors():
    config_path = Path(__file__).resolve().parents[1] / "config" / "competitors.yaml"
    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    competitors = config.get("competitors") if config else None
    if not isinstance(competitors, list):
        raise ValueError(f"{config_path} must define a 'competitors' list.")
    return competitors

async def process_url(competitor_name, url_entry):
    url = url_entry["url"]
    page_type = url_entry["type"]

    print(f"\n{'='*50}")
    print(f"Processing: {competitor_name} | {page_type}")
    print(f"URL: {url}")
    print(f"{'='*50}")

    scraped_text = await scrape_url(url)

    if not scraped_text:
        print(f"Skipping analysis — scrape failed for {url}")
        return None

    print(f"Scraped {len(scraped_text)} characters")

    analysis = await analyse_url(
        competitor=competitor_name,
        url=url,
        page_type=page_type,
        new_text=scraped_text
    )

    return analysis

async def run_crawler(max_concurrent=2):
    if max_concurrent < 1:
        raise ValueError("max_concurrent must be at least 1.")
    with logfire.span("crawler.run_crawler") as span:
        competitors = load_competitors()
        all_analyses = []
        errors = 0

        print(f"Starting crawler for {len(competitors)} competitors...")

        for competitor in competitors:
            competitor_name = competitor["name"]
            urls = competitor["urls"]

            print(f"\nProcessing competitor: {competitor_name} ({len(urls)} URLs)")

            for i in range(0, len(urls), max_concurrent):
                batch = urls[i:i + max_concurrent]

                tasks = [
                    process_url(competitor_name, url_entry)
                    for url_entry in batch
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, Exception):
                        print(f"Error in batch: {result}")
                        errors += 1
                    elif result is not None:
                        all_analyses.append(result)

                await asyncio.sleep(3)

        span.set_attributes({
            "competitors_count": len(competitors),
            "analyses_produced": len(all_analyses),
            "errors": errors,
        })
        print(f"\nCrawler complete. Got {len(all_analyses)} analyses.")
        return all_analyses
