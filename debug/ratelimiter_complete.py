"""
TEST COMPLETO: Rate Limiter + Groq API + ZIP Real

Este test valida:
1. Funcionamiento del rate limiter con Token Bucket
2. Integración con Groq API real
3. Procesamiento de ZIP completo
4. Generación de documentación
"""

import sys
import os
import time
import logging
import zipfile
import io
from datetime import datetime

# Setup path
sys.path.insert(0, '.')

from api.services.rate_limiter import Ratelimiter
from api.services.documentation_orchestrator import DocumentationOrchestrator
from api.services.ai import DocumentadorIA
from api.services.zip_services import ZipService
from api.services.chunking_service import ChunkingService
from api.services.cache_service import CacheService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Color codes para terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class RateLimiterTest:
    """Test suite para el rate limiter"""
    
    def __init__(self):
        self.results = {
            "test_ratelimiter": {},
            "test_groq_integration": {},
            "test_zip_processing": {}
        }
        self.start_time = None
        self.total_tokens_used = 0
        self.total_requests = 0
        
    def print_header(self, title):
        """Imprime encabezado de sección"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{title:^70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}\n")
    
    def print_test(self, name, status, message=""):
        """Imprime resultado de test"""
        if status == "PASS":
            symbol = f"{Colors.OKGREEN}✓{Colors.ENDC}"
        elif status == "FAIL":
            symbol = f"{Colors.FAIL}✗{Colors.ENDC}"
        else:
            symbol = f"{Colors.WARNING}!{Colors.ENDC}"
        
        print(f"{symbol} {Colors.BOLD}{name}{Colors.ENDC}: {status}")
        if message:
            print(f"  → {message}")
    
    def test_ratelimiter_basic(self):
        """Test 1: Verificar funcionamiento básico del rate limiter"""
        self.print_header("TEST 1: Rate Limiter - Funcionamiento Básico")
        
        try:
            # Crear limiter con límites bajos para testing rápido
            limiter = Ratelimiter(
                req_per_min=10,           # 10 requests por minuto
                tokens_per_min=1000,      # 1000 tokens por minuto
                burst_factor=1.0,
                key_prefix="test:basic"
            )
            
            logger.info("Rate Limiter inicializado")
            
            # Test 1.1: Primera request debe pasar
            request1 = limiter.allow_request(tokens_requested=100)
            self.print_test(
                "Request 1 (100 tokens)",
                "PASS" if request1 else "FAIL",
                f"Permitida: {request1}"
            )
            self.results["test_ratelimiter"]["request_1"] = request1
            
            # Test 1.2: Segunda request inmediata debe pasar
            request2 = limiter.allow_request(tokens_requested=200)
            self.print_test(
                "Request 2 (200 tokens)",
                "PASS" if request2 else "FAIL",
                f"Permitida: {request2}"
            )
            self.results["test_ratelimiter"]["request_2"] = request2
            
            # Test 1.3: Muchas requests deben agotar
            requests_count = 0
            for i in range(20):
                allowed = limiter.allow_request(tokens_requested=100)
                if allowed:
                    requests_count += 1
                else:
                    logger.info(f"Rate limit alcanzado en request {i+1}")
                    break
            
            self.print_test(
                "Rate Limiting (agotamiento)",
                "PASS" if requests_count < 20 else "FAIL",
                f"Se permitieron {requests_count}/20 requests antes de agotar"
            )
            self.results["test_ratelimiter"]["rate_limit_effective"] = requests_count < 20
            
            # Test 1.4: Esperar y verificar recuperación (necesita ~15 segundos para recuperarse)
            logger.info("Esperando 20 segundos para recuperación de tokens...")
            time.sleep(20)
            request_after_wait = limiter.allow_request(tokens_requested=100)
            self.print_test(
                "Recuperación tras espera (20s)",
                "PASS" if request_after_wait else "FAIL",
                f"Permitida tras espera: {request_after_wait}"
            )
            self.results["test_ratelimiter"]["recovery"] = request_after_wait
            
            return all(self.results["test_ratelimiter"].values())
            
        except Exception as e:
            self.print_test(
                "Rate Limiter Básico",
                "FAIL",
                f"Exception: {str(e)}"
            )
            logger.exception("Error en test_ratelimiter_basic")
            return False
    
    def test_groq_integration(self):
        """Test 2: Integración con Groq API"""
        self.print_header("TEST 2: Integración Groq API + Rate Limiter")
        
        try:
            # Verificar que tenemos API key (busca tanto GROQ_API_KEY como API_KEY)
            api_key = os.getenv("GROQ_API_KEY") or os.getenv("API_KEY")
            if not api_key:
                self.print_test(
                    "API_KEY (GROQ_API_KEY o API_KEY)",
                    "FAIL",
                    "Variable de entorno GROQ_API_KEY o API_KEY no configurada"
                )
                return False
            
            self.print_test(
                "API_KEY (GROQ_API_KEY o API_KEY)",
                "PASS",
                "Variable de entorno configurada"
            )
            
            # Crear servicio IA
            logger.info("Inicializando DocumentadorIA...")
            documentador = DocumentadorIA()
            
            self.print_test(
                "DocumentadorIA",
                "PASS",
                "Inicializado con limiters para cada modelo"
            )
            
            # Test 2.1: Estimación de tokens
            system = "You are a programmer"
            user = "def hello(): return 'Hello World'"
            
            tokens = documentador.estimate_tokens(system, user)
            self.print_test(
                "Token Estimation",
                "PASS",
                f"Sistema: {len(system)} chars + User: {len(user)} chars → {tokens} tokens estimados"
            )
            self.results["test_groq_integration"]["token_estimation"] = tokens > 0
            
            # Test 2.2: Generar documentación simple
            logger.info("Generando documentación simple...")
            simple_code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)
            """
            
            start = time.time()
            try:
                doc = documentador.generar(
                    codigo_fuente=simple_code,
                    tipo="markdown",
                    lang="en",
                    is_chunk=False
                )
                elapsed = time.time() - start
                
                self.print_test(
                    "Documentación Simple (Groq API)",
                    "PASS",
                    f"Generada en {elapsed:.2f}s ({len(doc)} caracteres)"
                )
                self.results["test_groq_integration"]["groq_api_call"] = True
                self.total_requests += 1
                
            except Exception as e:
                self.print_test(
                    "Documentación Simple (Groq API)",
                    "FAIL",
                    f"Error: {str(e)}"
                )
                self.results["test_groq_integration"]["groq_api_call"] = False
                return False
            
            return True
            
        except Exception as e:
            self.print_test(
                "Groq Integration",
                "FAIL",
                f"Exception: {str(e)}"
            )
            logger.exception("Error en test_groq_integration")
            return False
    
    def test_zip_processing(self):
        """Test 3: Procesamiento de ZIP completo con rate limiting"""
        self.print_header("TEST 3: Procesamiento ZIP + Rate Limiter")
        
        try:
            # Crear un ZIP de prueba con archivos HTML/JS
            logger.info("Creando ZIP de prueba...")
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zf:
                # Archivo 1: HTML
                zf.writestr('index.html', '''
<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
</head>
<body>
    <h1>Hello World</h1>
    <script src="script.js"></script>
</body>
</html>
                ''')
                
                # Archivo 2: JavaScript
                zf.writestr('script.js', '''
function greet(name) {
    return "Hello, " + name;
}

document.addEventListener('DOMContentLoaded', function() {
    console.log(greet('World'));
});
                ''')
                
                # Archivo 3: CSS
                zf.writestr('style.css', '''
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
}

h1 {
    color: #333;
}
                ''')
            
            zip_content = zip_buffer.getvalue()
            self.print_test(
                "ZIP Creation",
                "PASS",
                f"ZIP creado con 3 archivos ({len(zip_content):,} bytes)"
            )
            self.results["test_zip_processing"]["zip_creation"] = True
            
            # Crear orquestador
            logger.info("Inicializando DocumentationOrchestrator...")
            orch = DocumentationOrchestrator(
                max_input_size=10*1024*1024,
                max_files=50,
                chunking_service=ChunkingService(max_chunk_size=5000),
                cache_service=CacheService(max_size=100)
            )
            
            # Procesar ZIP
            logger.info("Procesando ZIP con orquestador...")
            start = time.time()
            
            try:
                result = orch.process_zip(
                    zip_content,
                    doc_type='markdown',
                    extra_requirements='Include code examples',
                    language='en'
                )
                elapsed = time.time() - start
                
                metadata = result['metadata']
                self.print_test(
                    "ZIP Processing",
                    "PASS",
                    f"Procesado en {elapsed:.2f}s"
                )
                self.print_test(
                    "Files Processed",
                    "PASS",
                    f"{metadata['total_files']} archivos → {metadata['total_chunks']} chunks"
                )
                self.print_test(
                    "Cache Stats",
                    "PASS",
                    f"Hit rate: {metadata['cache_stats']['hit_rate_percent']}%"
                )
                
                self.results["test_zip_processing"]["zip_processing"] = True
                self.results["test_zip_processing"]["metadata"] = metadata
                self.total_requests += metadata['total_chunks']
                
            except Exception as e:
                self.print_test(
                    "ZIP Processing",
                    "FAIL",
                    f"Error: {str(e)}"
                )
                self.results["test_zip_processing"]["zip_processing"] = False
                logger.exception("Error procesando ZIP")
                return False
            
            return True
            
        except Exception as e:
            self.print_test(
                "ZIP Test",
                "FAIL",
                f"Exception: {str(e)}"
            )
            logger.exception("Error en test_zip_processing")
            return False
    
    def run_all_tests(self):
        """Ejecuta todos los tests"""
        self.start_time = time.time()
        
        print(f"\n{Colors.BOLD}{Colors.OKCYAN}")
        print("╔" + "="*68 + "╗")
        print("║" + "RATE LIMITER + GROQ API TEST SUITE".center(68) + "║")
        print("║" + datetime.now().strftime("%Y-%m-%d %H:%M:%S").center(68) + "║")
        print("╚" + "="*68 + "╝")
        print(f"{Colors.ENDC}\n")
        
        # Ejecutar tests
        test1_pass = self.test_ratelimiter_basic()
        test2_pass = self.test_groq_integration()
        test3_pass = self.test_zip_processing()
        
        total_elapsed = time.time() - self.start_time
        
        # Generar reporte
        self.generate_report(test1_pass, test2_pass, test3_pass, total_elapsed)
        
        return test1_pass and test2_pass and test3_pass
    
    def generate_report(self, t1, t2, t3, elapsed):
        """Genera reporte final"""
        self.print_header("FINAL REPORT / BOLETÍN FINAL")
        
        total_tests = 3
        passed_tests = sum([t1, t2, t3])
        
        print(f"{Colors.BOLD}Resumen de Tests:{Colors.ENDC}")
        print(f"  Total: {total_tests} tests")
        print(f"  ✓ Pasados: {passed_tests}")
        print(f"  ✗ Fallidos: {total_tests - passed_tests}")
        print(f"  Tiempo total: {elapsed:.2f} segundos\n")
        
        print(f"{Colors.BOLD}Resultados Detallados:{Colors.ENDC}")
        print(f"  Test 1 (Rate Limiter Básico): {'PASS' if t1 else 'FAIL'}")
        print(f"  Test 2 (Groq Integration): {'PASS' if t2 else 'FAIL'}")
        print(f"  Test 3 (ZIP Processing): {'PASS' if t3 else 'FAIL'}\n")
        
        print(f"{Colors.BOLD}Estadísticas:{Colors.ENDC}")
        print(f"  Total de requests: {self.total_requests}")
        print(f"  Promedio por request: {elapsed/max(self.total_requests, 1):.2f}s\n")
        
        # Guardar reporte en archivo
        report_file = "test_results.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("RATE LIMITER + GROQ API TEST RESULTS\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*70 + "\n\n")
            
            f.write("SUMMARY\n")
            f.write("-"*70 + "\n")
            f.write(f"Total Tests: {total_tests}\n")
            f.write(f"Passed: {passed_tests}\n")
            f.write(f"Failed: {total_tests - passed_tests}\n")
            f.write(f"Duration: {elapsed:.2f}s\n\n")
            
            f.write("DETAILED RESULTS\n")
            f.write("-"*70 + "\n")
            f.write(f"Test 1 - Rate Limiter Basic: {'PASS' if t1 else 'FAIL'}\n")
            f.write(f"  Results: {self.results['test_ratelimiter']}\n\n")
            
            f.write(f"Test 2 - Groq Integration: {'PASS' if t2 else 'FAIL'}\n")
            f.write(f"  Results: {self.results['test_groq_integration']}\n\n")
            
            f.write(f"Test 3 - ZIP Processing: {'PASS' if t3 else 'FAIL'}\n")
            f.write(f"  Results: {self.results['test_zip_processing']}\n\n")
            
            f.write("STATISTICS\n")
            f.write("-"*70 + "\n")
            f.write(f"Total Requests: {self.total_requests}\n")
            f.write(f"Avg Time per Request: {elapsed/max(self.total_requests, 1):.2f}s\n")
        
        print(f"{Colors.OKGREEN}✓ Reporte guardado en: {report_file}{Colors.ENDC}")
        
        # Imprimir conclusión
        if passed_tests == total_tests:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ TODOS LOS TESTS PASARON{Colors.ENDC}")
            print(f"  El rate limiter funciona correctamente con Groq API")
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}✗ ALGUNOS TESTS FALLARON{Colors.ENDC}")
            print(f"  Revisar logs arriba para más detalles")


if __name__ == "__main__":
    test = RateLimiterTest()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)
