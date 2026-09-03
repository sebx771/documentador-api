models = {
    "chunking": {
        "provider": "groq",
        "id": "llama-3.3-70b-versatile",
        "tpm": 12000
    },
    "final_doc": {
        "provider": "openrouter",
        "id": "google/gemma-4-31b-it:free",
        "tpm": 100000
    },
    "fallback": {
        "provider": "openrouter",
        "id": "z-ai/glm-5.2:free",
        "tpm": 80000
    },
    "emergency": {
        "provider": "openrouter",
        "id": "cohere/north-mini-code:free",
        "tpm": 50000
    }
}