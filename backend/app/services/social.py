"""
Curato AI — Social Provider Interface
"""

import os
import asyncio
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel
from app.core.logging import get_logger
from app.services.search import get_search_provider

logger = get_logger(__name__)


class SocialPost(BaseModel):
    id: str
    author: str
    content: str
    url: str
    score: int | None = None
    published_at: str | None = None


class SocialProvider(ABC):
    """Abstract interface for Social Network data (Reddit)."""
    
    @abstractmethod
    async def get_top_posts(self, forum: str, limit: int = 10) -> list[SocialPost]:
        pass


class LinkedInProvider(ABC):
    """Abstract interface for LinkedIn competitor intelligence."""
    
    @abstractmethod
    async def get_company_posts(self, company_name: str, limit: int = 5) -> list[SocialPost]:
        pass
        
    @abstractmethod
    async def get_trending_topics(self) -> list[SocialPost]:
        pass


# ── Reddit Implementation (PRAW) ─────────────────────────────────────────────

class RedditProvider(SocialProvider):
    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        self.client_id = client_id or os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = "CuratoAI/1.0"
        
    async def get_top_posts(self, forum: str, limit: int = 10) -> list[SocialPost]:
        if not self.client_id or not self.client_secret:
            logger.warning("Reddit API credentials not found. Returning empty.")
            return []
            
        import praw
        
        def _fetch():
            reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
            
            subreddit = reddit.subreddit(forum)
            posts = []
            for submission in subreddit.hot(limit=limit):
                posts.append(SocialPost(
                    id=submission.id,
                    author=submission.author.name if submission.author else "[deleted]",
                    content=f"Title: {submission.title}\n\n{submission.selftext}",
                    url=f"https://reddit.com{submission.permalink}",
                    score=submission.score,
                    published_at=str(submission.created_utc)
                ))
            return posts
            
        try:
            return await asyncio.to_thread(_fetch)
        except Exception as e:
            logger.error("Reddit fetch failed", error=str(e))
            return []


# ── LinkedIn Fallback Implementation ─────────────────────────────────────────

class SearchFallbackLinkedInProvider(LinkedInProvider):
    """
    Fallback LinkedIn provider that uses Tavily/Google Search operators 
    instead of direct scraping.
    """
    def __init__(self):
        self.search = get_search_provider()
        
    async def get_company_posts(self, company_name: str, limit: int = 5) -> list[SocialPost]:
        # Perform a search for recent posts on LinkedIn
        query = f'site:linkedin.com/posts "{company_name}"'
        try:
            results = await self.search.search(query=query, num_results=limit)
            posts = []
            for idx, res in enumerate(results):
                posts.append(SocialPost(
                    id=f"search_{idx}",
                    author=company_name,
                    content=res.snippet,
                    url=res.url
                ))
            return posts
        except Exception as e:
            logger.error("LinkedIn fallback search failed", error=str(e))
            return []

    async def get_trending_topics(self) -> list[SocialPost]:
        query = 'site:linkedin.com/pulse OR site:linkedin.com/posts "marketing trends" OR "social media"'
        try:
            results = await self.search.news(topic=query, days_back=7, num_results=5)
            posts = []
            for idx, res in enumerate(results):
                posts.append(SocialPost(
                    id=f"trend_{idx}",
                    author="various",
                    content=f"{res.title}\n{res.snippet}",
                    url=res.url
                ))
            return posts
        except Exception:
            return []


# ── Factories ────────────────────────────────────────────────────────────────

def get_reddit_provider() -> SocialProvider:
    return RedditProvider()

def get_linkedin_provider() -> LinkedInProvider:
    return SearchFallbackLinkedInProvider()
