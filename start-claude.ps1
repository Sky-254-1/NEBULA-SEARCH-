# Claude Code Launcher for Windows (PowerShell)
# Sets OpenRouter base URL and launches Claude Code interactively.
# NOTE: set your own API key in the environment; never commit secrets.
# Point Claude Code at OpenRouter instead of Anthropic
$env:ANTHROPIC_BASE_URL = "https://openrouter.ai/api/v1"

# Launch Claude Code interactively
claude
