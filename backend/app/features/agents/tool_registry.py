"""
Curato AI — Tool Registry (MCP-Compatible Abstraction)

A generic, extensible tool registry that allows agents to invoke
external integrations without being directly coupled to them.

Inspired by the Model Context Protocol (MCP), this provides:
1. A standard tool interface (BaseTool)
2. A central registry for tool discovery
3. Per-agent tool access control
4. Structured input/output contracts

Future integrations (Google Search, Tavily, Reddit, LinkedIn, Google Trends,
news APIs, web scraping) can be added by implementing BaseTool and
registering them — zero changes to existing agents required.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from app.core.exceptions import ToolExecutionError
from app.core.logging import get_logger

from app.services.search import get_search_provider
from app.services.trends import get_trend_provider
from app.services.scraping import get_scraper_provider
from app.services.social import get_reddit_provider, get_linkedin_provider

logger = get_logger(__name__)


# =============================================================================
# Tool Interface
# =============================================================================


class ToolParameter(BaseModel):
    """Describes a single parameter for a tool."""

    name: str
    type: str  # "string", "integer", "boolean", "object", "array"
    description: str = ""
    required: bool = True
    default: Any = None


class ToolSchema(BaseModel):
    """Describes a tool's interface — name, description, and parameters."""

    name: str
    display_name: str = ""
    description: str = ""
    category: str = "general"  # research, content, integration, utility
    parameters: list[ToolParameter] = Field(default_factory=list)
    returns_description: str = ""


class ToolResult(BaseModel):
    """Standardized result from a tool execution."""

    success: bool = True
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseTool(ABC):
    """
    Abstract base class for all tools in the Curato AI system.

    Every external integration (search, scraping, APIs) implements this
    interface. Tools are registered in the ToolRegistry and can be
    invoked by agents through the orchestrator.

    MCP Compatibility:
    - Each tool exposes a schema (ToolSchema) describing its interface
    - Input/output is always structured (JSON-serializable)
    - Tools are stateless — no side effects between invocations
    """

    @property
    @abstractmethod
    def schema(self) -> ToolSchema:
        """Return the tool's schema describing its interface."""
        ...

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute the tool with the given parameters.

        Returns a ToolResult with structured data.
        Implementations should catch their own exceptions and return
        ToolResult(success=False, error=...) rather than raising.
        """
        ...

    async def validate_params(self, **kwargs: Any) -> bool:
        """Validate input parameters against the schema. Override for custom validation."""
        required = {p.name for p in self.schema.parameters if p.required}
        provided = set(kwargs.keys())
        missing = required - provided
        if missing:
            raise ToolExecutionError(
                message=f"Missing required parameters: {missing}",
                tool_name=self.schema.name,
            )
        return True

    def to_mcp_format(self) -> dict[str, Any]:
        """Export tool schema in MCP-compatible format."""
        return {
            "name": self.schema.name,
            "description": self.schema.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    p.name: {
                        "type": p.type,
                        "description": p.description,
                        **({"default": p.default} if p.default is not None else {}),
                    }
                    for p in self.schema.parameters
                },
                "required": [p.name for p in self.schema.parameters if p.required],
            },
        }


# =============================================================================
# Built-in Tool Stubs (Placeholders for future integrations)
# =============================================================================


class WebSearchTool(BaseTool):
    """Web search integration."""
    
    def __init__(self):
        self.provider = get_search_provider()

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="web_search",
            display_name="Web Search",
            description="Search the web for information on a given query",
            category="research",
            parameters=[
                ToolParameter(name="query", type="string", description="Search query"),
                ToolParameter(
                    name="num_results",
                    type="integer",
                    description="Number of results to return",
                    required=False,
                    default=10,
                ),
            ],
            returns_description="List of search results with title, URL, and snippet",
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = kwargs.get("query")
        num_results = kwargs.get("num_results", 10)
        try:
            results = await self.provider.search(query=query, num_results=num_results)
            data = [res.model_dump() for res in results]
            return ToolResult(
                success=True,
                data={"results": data, "query": query},
                metadata={"provider": self.provider.__class__.__name__},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), data={"results": [], "query": query})


class NewsAPITool(BaseTool):
    """News search integration."""
    
    def __init__(self):
        self.provider = get_search_provider()

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="news_api",
            display_name="News API",
            description="Fetch latest news articles on a given topic",
            category="research",
            parameters=[
                ToolParameter(name="topic", type="string", description="News topic"),
                ToolParameter(
                    name="days_back",
                    type="integer",
                    description="How many days back to search",
                    required=False,
                    default=7,
                ),
            ],
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        topic = kwargs.get("topic")
        days_back = kwargs.get("days_back", 7)
        try:
            results = await self.provider.news(topic=topic, days_back=days_back, num_results=10)
            data = [res.model_dump() for res in results]
            return ToolResult(
                success=True,
                data={"articles": data, "topic": topic},
                metadata={"provider": self.provider.__class__.__name__},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), data={"articles": [], "topic": topic})


class GoogleTrendsTool(BaseTool):
    """Google Trends integration."""
    
    def __init__(self):
        self.provider = get_trend_provider()

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="google_trends",
            display_name="Google Trends",
            description="Get trending topics and search volume data",
            category="research",
            parameters=[
                ToolParameter(name="keywords", type="array", description="Keywords to analyze"),
                ToolParameter(
                    name="region",
                    type="string",
                    description="Geographic region",
                    required=False,
                    default="US",
                ),
            ],
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        keywords = kwargs.get("keywords", [])
        region = kwargs.get("region", "US")
        try:
            results = await self.provider.get_trends(keywords=keywords, region=region)
            data = [res.model_dump() for res in results]
            return ToolResult(
                success=True,
                data={"trends": data, "keywords": keywords},
                metadata={"provider": self.provider.__class__.__name__},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), data={"trends": [], "keywords": keywords})


class WebScraperTool(BaseTool):
    """Web scraping tool with layered fallbacks."""
    
    def __init__(self):
        self.provider = get_scraper_provider()

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="web_scraper",
            display_name="Web Scraper",
            description="Scrape content from a given URL to markdown",
            category="research",
            parameters=[
                ToolParameter(name="url", type="string", description="URL to scrape"),
            ],
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        url = kwargs.get("url")
        try:
            res = await self.provider.scrape(url=url)
            return ToolResult(
                success=True,
                data=res.model_dump(),
                metadata={"provider": res.provider_used},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), data={"content": "", "url": url})


class LinkedInTool(BaseTool):
    """LinkedIn integration."""
    
    def __init__(self):
        self.provider = get_linkedin_provider()

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="linkedin",
            display_name="LinkedIn",
            description="Fetch LinkedIn engagement data and trending content",
            category="research",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="Action to perform (trending, company_posts:<name>)",
                ),
            ],
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "")
        try:
            if action.startswith("company_posts:"):
                company = action.split(":", 1)[1]
                posts = await self.provider.get_company_posts(company)
            else:
                posts = await self.provider.get_trending_topics()
                
            data = [p.model_dump() for p in posts]
            return ToolResult(
                success=True,
                data={"results": data},
                metadata={"provider": self.provider.__class__.__name__},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), data={"results": []})


class RedditTool(BaseTool):
    """Reddit integration."""
    
    def __init__(self):
        self.provider = get_reddit_provider()

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="reddit",
            display_name="Reddit",
            description="Search Reddit for discussions and trending topics",
            category="research",
            parameters=[
                ToolParameter(name="subreddit", type="string", description="Subreddit to search"),
                ToolParameter(name="query", type="string", description="Search query"),
            ],
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        subreddit = kwargs.get("subreddit")
        try:
            posts = await self.provider.get_top_posts(forum=subreddit)
            data = [p.model_dump() for p in posts]
            return ToolResult(
                success=True,
                data={"posts": data},
                metadata={"provider": self.provider.__class__.__name__},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), data={"posts": []})


# =============================================================================
# Tool Registry
# =============================================================================


class ToolRegistry:
    """
    Central registry for all tools available to agents.

    Tools are registered by name and can be discovered, filtered by
    category, and invoked by agents through the orchestrator.

    Usage:
        registry = ToolRegistry()
        registry.register(WebSearchTool())
        result = await registry.invoke("web_search", query="AI trends")
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool in the registry."""
        name = tool.schema.name
        self._tools[name] = tool
        logger.info("Tool registered", tool=name, category=tool.schema.category)

    def unregister(self, tool_name: str) -> None:
        """Remove a tool from the registry."""
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.info("Tool unregistered", tool=tool_name)

    def get(self, tool_name: str) -> BaseTool | None:
        """Get a tool by name."""
        return self._tools.get(tool_name)

    def list_tools(self, category: str | None = None) -> list[ToolSchema]:
        """List all registered tools, optionally filtered by category."""
        schemas = [tool.schema for tool in self._tools.values()]
        if category:
            schemas = [s for s in schemas if s.category == category]
        return schemas

    def get_tools_for_agent(self, tool_names: list[str]) -> list[BaseTool]:
        """Get specific tools by name (for per-agent access control)."""
        return [self._tools[name] for name in tool_names if name in self._tools]

    def get_mcp_schemas(self, tool_names: list[str] | None = None) -> list[dict[str, Any]]:
        """Export tool schemas in MCP-compatible format."""
        tools = self._tools.values()
        if tool_names:
            tools = [t for t in tools if t.schema.name in tool_names]
        return [tool.to_mcp_format() for tool in tools]

    async def invoke(self, tool_name: str, **kwargs: Any) -> ToolResult:
        """Invoke a tool by name with given parameters."""
        tool = self._tools.get(tool_name)
        if tool is None:
            raise ToolExecutionError(
                message=f"Tool '{tool_name}' not found in registry",
                tool_name=tool_name,
            )

        await tool.validate_params(**kwargs)
        logger.info("Invoking tool", tool=tool_name, params=list(kwargs.keys()))

        try:
            result = await tool.execute(**kwargs)
            logger.info("Tool execution completed", tool=tool_name, success=result.success)
            return result
        except ToolExecutionError:
            raise
        except Exception as e:
            logger.error("Tool execution failed", tool=tool_name, error=str(e))
            raise ToolExecutionError(
                message=f"Tool '{tool_name}' failed: {str(e)}",
                tool_name=tool_name,
            )


# ── Factory ──────────────────────────────────────────────────────────────────


def create_default_tool_registry() -> ToolRegistry:
    """Create a ToolRegistry with all built-in tools pre-registered."""
    registry = ToolRegistry()
    registry.register(WebSearchTool())
    registry.register(NewsAPITool())
    registry.register(GoogleTrendsTool())
    registry.register(WebScraperTool())
    registry.register(LinkedInTool())
    registry.register(RedditTool())
    return registry


# ── Singleton ────────────────────────────────────────────────────────────────
_tool_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """Get or create the singleton ToolRegistry."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = create_default_tool_registry()
    return _tool_registry
