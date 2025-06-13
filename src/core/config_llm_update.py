# Add these fields to your Settings class in config.py:

    # LLM Settings
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_llm_provider: Optional[str] = "openai"  # or "anthropic"
