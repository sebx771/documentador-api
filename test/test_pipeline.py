import sys
sys.path.insert(0, '.')

from api.services.zip_services import ZipService
from api.services.documentation_orchestrator import DocumentationOrchestrator
from api.services.chunking_service import ChunkingService
from api.services.cache_service import CacheService

ZIP_FILE = 'ejercicios_javascript.zip'

def test_zip_processing():
    print("=" * 50)
    print("Test: ZIP Processing Pipeline")
    print("=" * 50)
    
    with open(ZIP_FILE, 'rb') as f:
        zip_content = f.read()
    
    print(f"\n[1] ZIP cargado: {len(zip_content):,} bytes")
    
    print("\n[2] Extrayendo archivos con ZipService...")
    zs = ZipService()
    raw_code, invalid_files = zs.extraer_zip(zip_content)
    print(f"    Código extraído: {len(raw_code):,} caracteres")
    print(f"    Archivos inválidos: {len(invalid_files)}")
    
    print("\n[3] Procesando con DocumentationOrchestrator...")
    orch = DocumentationOrchestrator(
        max_input_size=10*1024*1024,
        max_files=50,
        chunking_service=ChunkingService(max_chunk_size=8000, max_files_per_chunk=10),
        cache_service=CacheService(max_size=100)
    )
    
    try:
        result = orch.process_zip(zip_content, 'markdown', '', zip_service=zs)
        
        print("\n[4] Resultado:")
        print(f"    Archivos procesados: {result['metadata']['total_files']}")
        print(f"    Chunks generados: {result['metadata']['total_chunks']}")
        print(f"    Tiempo: {result['metadata']['elapsed_time_seconds']}s")
        print(f"    Cache hit rate: {result['metadata']['cache_stats']['hit_rate_percent']}%")
        print(f"    Docs length: {len(result['documentation']):,} chars")
        
        print("\n[5] Cache stats:")
        stats = result['metadata']['cache_stats']
        print(f"    Hits: {stats['hits']}")
        print(f"    Misses: {stats['misses']}")
        print(f"    Evictions: {stats['evictions']}")
        
        print("\n" + "=" * 50)
        print("SUCCESS - Pipeline funcionando correctamente")
        print("=" * 50)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    test_zip_processing()