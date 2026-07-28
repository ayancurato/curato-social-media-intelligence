"""
Curato AI — Web Scraper Provider Interface
"""

import os
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel
from app.core.logging import get_logger

logger = get_logger(__name__)


class ScrapedContent(BaseModel):
    url: str
    markdown: str
    metadata: dict[str, Any]
    provider_used: str


class ScraperProvider(ABC):
    """Abstract interface for website scraping."""
    
    @abstractmethod
    async def scrape(self, url: str) -> ScrapedContent:
        """Fetch and convert a URL to markdown content."""
        pass


# ── Implementations ──────────────────────────────────────────────────────────

class FirecrawlScraper(ScraperProvider):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        
    async def scrape(self, url: str) -> ScrapedContent:
        if not self.api_key:
            raise ValueError("Firecrawl API key not configured")
            
        import asyncio
        from firecrawl import FirecrawlApp
        
        def _scrape():
            app = FirecrawlApp(api_key=self.api_key)
            return app.scrape_url(url, params={'formats': ['markdown']})
            
        res = await asyncio.to_thread(_scrape)
        
        return ScrapedContent(
            url=url,
            markdown=res.get("markdown", ""),
            metadata=res.get("metadata", {}),
            provider_used="firecrawl"
        )


class Crawl4AIScraper(ScraperProvider):
    async def scrape(self, url: str) -> ScrapedContent:
        # Stub for Crawl4AI
        # In a real setup, we would import crawl4ai and run its crawler
        raise NotImplementedError("Crawl4AI not fully configured. Falling back.")


class PlaywrightScraper(ScraperProvider):
    async def scrape(self, url: str) -> ScrapedContent:
        # Use playwright to load dynamic content
        try:
            from playwright.async_api import async_playwright
            import markdownify
        except ImportError:
            raise NotImplementedError("Playwright/markdownify not installed.")
            
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle")
            html = await page.content()
            await browser.close()
            
            md = markdownify.markdownify(html, heading_style="ATX")
            
            return ScrapedContent(
                url=url,
                markdown=md,
                metadata={"dynamic": True},
                provider_used="playwright"
            )


class BeautifulSoupScraper(ScraperProvider):
    async def scrape(self, url: str) -> ScrapedContent:
        import httpx
        from bs4 import BeautifulSoup
        import markdownify
        
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Remove scripts, styles
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
                
            md = markdownify.markdownify(str(soup), heading_style="ATX")
            
            return ScrapedContent(
                url=url,
                markdown=md,
                metadata={"title": soup.title.string if soup.title else ""},
                provider_used="beautifulsoup"
            )


class LayeredScraperProvider(ScraperProvider):
    """
    Implements a fallback strategy:
    Firecrawl -> Crawl4AI -> Playwright -> BeautifulSoup
    """
    def __init__(self):
        self.chain = [
            FirecrawlScraper(),
            Crawl4AIScraper(),
            PlaywrightScraper(),
            BeautifulSoupScraper()
        ]
        
    async def scrape(self, url: str) -> ScrapedContent:
        last_error = None
        for scraper in self.chain:
            try:
                logger.info("Attempting scrape", provider=scraper.__class__.__name__, url=url)
                return await scraper.scrape(url)
            except Exception as e:
                logger.debug("Scraper failed, falling back", provider=scraper.__class__.__name__, error=str(e))
                last_error = e
                
        raise Exception(f"All scrapers failed. Last error: {str(last_error)}")


# ── Factory ──────────────────────────────────────────────────────────────────

def get_scraper_provider() -> ScraperProvider:
    return LayeredScraperProvider()
