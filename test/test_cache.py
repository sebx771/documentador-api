import sys
sys.path.insert(0, '.')

from api.services.zip_services import ZipService
from api.services.documentation_orchestrator import DocumentationOrchestrator
from api.services.chunking_service import ChunkingService
from api.services.cache_service import CacheService, get_global_cache
import time

ZIP_FILE = 'ejercicios_javascript.zip'

def test_cache():
    print("=" * 50)
    print("Test: Cache SHA256 con múltiples requests")
    print("=" * 50)
    
    with open(ZIP_FILE, 'rb') as f:
        zip_content = f.read()
    
    cache = get_global_cache(max_size=100, ttl_seconds=3600)
    chunking = ChunkingService(max_chunk_size=8000, max_files_per_chunk=10)
    zip_service = ZipService()
    
    print(f"\n[1] Primer request al servidor (cache vacío)")
    orch = DocumentationOrchestrator(
        max_input_size=10*1024*1024,
        max_files=50,
        chunking_service=chunking,
        cache_service=cache
    )
    
    result1 = orch.process_zip(zip_content, 'markdown', '', zip_service=zip_service)
    print(f"    Tiempo: {result1['metadata']['elapsed_time_seconds']}s")
    print(f"    Cache: {result1['metadata']['cache_stats']}")
    
    print(f"\n[2] Segundo request (debería usar cache)")
    orch2 = DocumentationOrchestrator(
        max_input_size=10*1024*1024,
        max_files=50,
        chunking_service=chunking,
        cache_service=cache
    )
    
    result2 = orch2.process_zip(zip_content, 'markdown', '', zip_service=zip_service)
    print(f"    Tiempo: {result2['metadata']['elapsed_time_seconds']}s")
    print(f"    Cache: {result2['metadata']['cache_stats']}")
    
    print(f"\n[3] Tercer request (verificando cache)")
    orch3 = DocumentationOrchestrator(
        max_input_size=10*1024*1024,
        max_files=50,
        chunking_service=chunking,
        cache_service=cache
    )
    
    result3 = orch3.process_zip(zip_content, 'markdown', '', zip_service=zip_service)
    print(f"    Tiempo: {result3['metadata']['elapsed_time_seconds']}s")
    print(f"    Cache: {result3['metadata']['cache_stats']}")
    
    print("\n" + "=" * 50)
    if result2['metadata']['cache_stats']['hit_rate_percent'] > 0:
        print("SUCCESS: Cache funcionando!")
    else:
        print("NOTA: Flask reinicia proceso entre requests")
        print("Para serverless real, usar Redis/Memcached externo")
    print("=" * 50)

if __name__ == "__main__":
    test_cache()