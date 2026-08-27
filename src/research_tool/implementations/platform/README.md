# Platform Adapter Implementations

Platform adapters provide URL pattern matching and platform-specific extraction hints (e.g. Shopee, TikTok, Facebook). Each must implement `PlatformAdapter` from `research_tool.interfaces`.

`GenericBrowserAdapter` provides basic fallbacks for standard web search patterns.
