import httpx
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv

load_dotenv()

def clean_text(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "meta", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text[:8000]

async def scrape_with_httpx(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return clean_text(response.text)
            else:
                print(f"httpx got status {response.status_code} for {url}")
                return None
    except Exception as e:
        print(f"httpx failed for {url}: {e}")
        return None

async def scrape_with_playwright(url):
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            html = await page.content()
            return clean_text(html)
    except Exception as e:
        print(f"Playwright failed for {url}: {e}")
        return None
    finally:
        if browser is not None:
            await browser.close()

async def scrape_url(url):
    print(f"Scraping: {url}")
    text = await scrape_with_httpx(url)
    if text and len(text) > 200:
        print(f"httpx succeeded for {url}")
        return text
    print(f"httpx insufficient, trying Playwright for {url}")
    text = await scrape_with_playwright(url)
    if text and len(text) > 200:
        print(f"Playwright succeeded for {url}")
        return text
    print(f"Both methods failed for {url}")
    return None

async def scrape_all_competitors(competitors):
    results = []
    for competitor in competitors:
        for url_entry in competitor["urls"]:
            text = await scrape_url(url_entry["url"])
            results.append({
                "competitor": competitor["name"],
                "url": url_entry["url"],
                "page_type": url_entry["type"],
                "text": text
            })
            await asyncio.sleep(2)
    return results
