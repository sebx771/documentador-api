models = {
    "chunking": {
        "provider": "openrouter",
        "id": "minimax/minimax-m3:free",
        "tpm": 60000
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