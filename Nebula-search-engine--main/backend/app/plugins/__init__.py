"""Plugin system for Nebula Search."""

from app.plugins.base import plugin_manager


def load_plugins():
    """Load and register all available search provider plugins."""
    if not plugin_manager.list_providers():
        # Load built-in plugins
        try:
            from app.plugins.providers.brave import BraveSearchProvider
            plugin_manager.register(BraveSearchProvider())
        except ImportError:
            pass
        
        # Add more providers as they are implemented
        # try:
        #     from app.plugins.providers.google import GoogleSearchProvider
        #     plugin_manager.register(GoogleSearchProvider())
        # except ImportError:
        #     pass


def get_plugin_manager():
    """Get the global plugin manager instance."""
    return plugin_manager