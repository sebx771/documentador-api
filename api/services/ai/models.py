

models = {

   "chunking": {
       "provider": "groq",
       "id": "meta-llama/llama-3.1-8b-instant",
       "tpm": 14000
   },
    "final_doc": {
        "provider": "groq",
        "id": "openai/gpt-oss-120b",
        "tpm": 8000
    },
    "fallback": {
        "provider": "groq",
        "id": "qwen/qwen3.6-27b",
        "tpm": 6000
    },
    "emergency": {
        "provider": "groq",
        "id": "openai/gpt-oss-20b",
        "tpm": 8000
    }
}
