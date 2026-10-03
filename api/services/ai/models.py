models = {
    "chunking": {
        "provider": "groq",
        "id": "openai/gpt-oss-120b",
        "tpm": 8000
    },
    "final_doc": {
        "provider": "gemini",
        "id": "gemini-3.8-flash",
        "tpm": 250000
    },
    "fallback": {
        "provider": "openrouter",
        "id": "liquid/lfm-2.5-2.6b:free",
        "tpm": 80000
    },
    "emergency": {
        "provider": "openrouter",
        "id": "cohere/north-mini-code:free",
        "tpm": 50000
    }
}