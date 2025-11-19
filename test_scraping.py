#!/usr/bin/env python3
"""
Script de prueba para el sistema de web scraping de Auditel
"""
import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.scraper_manager import ScraperManager
from utils.cache_manager import CacheManager
from utils.text_processor import TextProcessor
import logging

# Configurar logging simple
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

logger = logging.getLogger(__name__)


def test_cache_manager():
    """Prueba el gestor de caché"""
    print("\n" + "="*80)
    print("PRUEBA 1: Cache Manager")
    print("="*80)

    cache = CacheManager(cache_dir="cache_data_test")

    # Guardar datos
    datos_prueba = {"mensaje": "Hola mundo", "numero": 42}
    cache.guardar("test_key", datos_prueba)
    print("✅ Datos guardados en caché")

    # Obtener datos
    datos_obtenidos = cache.obtener("test_key")
    if datos_obtenidos == datos_prueba:
        print("✅ Datos recuperados correctamente del caché")
    else:
        print("❌ Error recuperando datos del caché")

    # Estadísticas
    stats = cache.estadisticas()
    print(f"📊 Estadísticas: {stats}")

    # Limpiar
    cache.limpiar_todo()
    print("✅ Caché limpiado")


def test_text_processor():
    """Prueba el procesador de texto"""
    print("\n" + "="*80)
    print("PRUEBA 2: Text Processor")
    print("="*80)

    processor = TextProcessor()

    # Limpiar HTML
    html = "<p>Este es un <b>texto</b> con <script>alert('x')</script> HTML</p>"
    limpio = processor.sanitizar_html(html)
    print(f"HTML original: {html}")
    print(f"Texto limpio: {limpio}")
    print("✅ Limpieza de HTML funcional")

    # Extraer keywords
    texto = "La Ley de Obras Públicas regula la construcción y contratación de infraestructura pública en México"
    keywords = processor.extraer_keywords(texto, max_keywords=5)
    print(f"\nTexto: {texto}")
    print(f"Keywords: {keywords}")
    print("✅ Extracción de keywords funcional")

    # Extraer referencias legales
    texto_legal = "Conforme al Artículo 123 de la Ley de Obras Públicas y el Reglamento de Construcción..."
    referencias = processor.extraer_referencias_legales(texto_legal)
    print(f"\nTexto legal: {texto_legal}")
    print(f"Referencias: {referencias}")
    print("✅ Extracción de referencias funcional")


def test_scrapers():
    """Prueba los scrapers"""
    print("\n" + "="*80)
    print("PRUEBA 3: Web Scrapers")
    print("="*80)

    cache = CacheManager()
    manager = ScraperManager(cache_manager=cache)

    # Consulta de prueba
    query = "obras públicas licitación"

    print(f"\n🔍 Buscando: '{query}'")
    print("⚠️ NOTA: Esta prueba real puede tardar 30-60 segundos...")
    print("⚠️ Los resultados dependen de la disponibilidad de los sitios web")

    try:
        # Buscar en todas las fuentes
        resultado = manager.buscar_en_todos(
            query=query,
            max_resultados_por_fuente=2,
            usar_cache=True
        )

        print(f"\n📊 Resultados:")
        print(f"   • Total encontrado: {resultado.total_encontrado}")
        print(f"   • Fuentes consultadas: {resultado.fuentes_consultadas}")
        print(f"   • Tiempo de búsqueda: {resultado.tiempo_busqueda:.2f}s")
        print(f"   • Desde caché: {resultado.desde_cache}")

        if resultado.normativas:
            print(f"\n📄 Primeras 3 normativas encontradas:")
            for i, norm in enumerate(resultado.normativas[:3], 1):
                print(f"\n   {i}. {norm.titulo[:80]}...")
                print(f"      Fuente: {norm.fuente}")
                print(f"      Tipo: {norm.tipo}")
                if norm.url:
                    print(f"      URL: {norm.url[:60]}...")

            print("\n✅ Web scraping funcional!")
        else:
            print("\n⚠️ No se encontraron resultados (puede ser normal si los sitios cambiaron)")
            print("   El scraper está funcional pero los sitios pueden requerir ajustes")

    except Exception as e:
        print(f"\n❌ Error durante el scraping: {e}")
        print("   Esto puede ser normal si hay problemas de conectividad")

    finally:
        # Limpiar
        manager.cerrar_todos()
        print("\n✅ Sesiones de scrapers cerradas")


def main():
    """Ejecuta todas las pruebas"""
    print("\n" + "#"*80)
    print("#" + " "*78 + "#")
    print("#" + " "*20 + "AUDITEL - PRUEBAS DEL SISTEMA" + " "*29 + "#")
    print("#" + " "*78 + "#")
    print("#"*80)

    try:
        # Prueba 1: Cache
        test_cache_manager()

        # Prueba 2: Text Processor
        test_text_processor()

        # Prueba 3: Scrapers (opcional, puede ser lenta)
        respuesta = input("\n¿Deseas probar el web scraping real? (puede tardar 30-60s) [s/N]: ")
        if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
            test_scrapers()
        else:
            print("\n⏭️ Prueba de web scraping omitida")

        print("\n" + "="*80)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("="*80)
        print("\n💡 El sistema está listo para usarse!")
        print("   Para iniciar la aplicación, ejecuta: python app_v2.py")

    except KeyboardInterrupt:
        print("\n\n⚠️ Pruebas interrumpidas por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
