"""Plugin system for Nebula Search."""

from app.plugins.base import plugin_manager


def load_plugins():
    """Load and register all available search provider plugins."""
    if not plugin_manager.list_providers():
        # Load built-in plugins
        providers = [
            ("brave", "app.plugins.providers.brave", "BraveSearchProvider"),
            ("google", "app.plugins.providers.google", "GoogleSearchProvider"),
            ("bing", "app.plugins.providers.bing", "BingSearchProvider"),
            ("duckduckgo", "app.plugins.providers.duckduckgo", "DuckDuckGoSearchProvider"),
        ]
        
        for provider_name, module_path, class_name in providers:
            try:
                module = __import__(module_path, fromlist=[class_name])
                provider_class = getattr(module, class_name)
                plugin_manager.register(provider_class())
            except (ImportError, AttributeError) as e:
                pass


def get_plugin_manager():
    """Get the global plugin manager instance."""
    return plugin_manager