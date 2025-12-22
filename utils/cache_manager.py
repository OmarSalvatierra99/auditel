"""
Gestor de caché para datos scrapeados
"""
import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger('auditel.cache')


class CacheManager:
    """Gestor de caché en disco con expiración"""

    def __init__(self, cache_dir: str = "cache_data", expiration_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.expiration_hours = expiration_hours
        self.cache_dir.mkdir(exist_ok=True)

        logger.info(f"CacheManager inicializado: {self.cache_dir}")

    def _generar_clave(self, identificador: str) -> str:
        """Genera una clave única para el caché"""
        return hashlib.md5(identificador.encode('utf-8')).hexdigest()

    def _ruta_archivo(self, clave: str) -> Path:
        """Obtiene la ruta del archivo de caché"""
        return self.cache_dir / f"{clave}.json"

    def guardar(self, identificador: str, datos: Any, metadata: Optional[Dict] = None) -> bool:
        """Guarda datos en el caché"""
        try:
            clave = self._generar_clave(identificador)
            ruta = self._ruta_archivo(clave)

            cache_data = {
                "identificador": identificador,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {},
                "datos": datos
            }

            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Datos guardados en caché: {identificador}")
            return True

        except Exception as e:
            logger.error(f"Error guardando en caché: {e}")
            return False

    def obtener(self, identificador: str) -> Optional[Any]:
        """Obtiene datos del caché si no han expirado"""
        try:
            clave = self._generar_clave(identificador)
            ruta = self._ruta_archivo(clave)

            if not ruta.exists():
                logger.debug(f"Caché miss: {identificador}")
                return None

            with open(ruta, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # Verificar expiración
            timestamp = datetime.fromisoformat(cache_data["timestamp"])
            expiracion = timestamp + timedelta(hours=self.expiration_hours)

            if datetime.now() > expiracion:
                logger.debug(f"Caché expirado: {identificador}")
                self.eliminar(identificador)
                return None

            logger.debug(f"Caché hit: {identificador}")
            return cache_data["datos"]

        except Exception as e:
            logger.error(f"Error obteniendo del caché: {e}")
            return None

    def eliminar(self, identificador: str) -> bool:
        """Elimina datos del caché"""
        try:
            clave = self._generar_clave(identificador)
            ruta = self._ruta_archivo(clave)

            if ruta.exists():
                ruta.unlink()
                logger.debug(f"Caché eliminado: {identificador}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error eliminando caché: {e}")
            return False

    def limpiar_expirados(self) -> int:
        """Limpia todos los archivos de caché expirados"""
        eliminados = 0

        try:
            for archivo in self.cache_dir.glob("*.json"):
                try:
                    with open(archivo, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)

                    timestamp = datetime.fromisoformat(cache_data["timestamp"])
                    expiracion = timestamp + timedelta(hours=self.expiration_hours)

                    if datetime.now() > expiracion:
                        archivo.unlink()
                        eliminados += 1

                except Exception as e:
                    logger.warning(f"Error procesando {archivo}: {e}")
                    continue

            logger.info(f"Limpieza de caché: {eliminados} archivos eliminados")
            return eliminados

        except Exception as e:
            logger.error(f"Error limpiando caché: {e}")
            return 0

    def limpiar_todo(self) -> bool:
        """Elimina todo el caché"""
        try:
            for archivo in self.cache_dir.glob("*.json"):
                archivo.unlink()

            logger.info("Caché completamente limpiado")
            return True

        except Exception as e:
            logger.error(f"Error limpiando todo el caché: {e}")
            return False

    def estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas del caché"""
        try:
            archivos = list(self.cache_dir.glob("*.json"))
            total = len(archivos)
            expirados = 0
            tamaño_total = 0

            for archivo in archivos:
                try:
                    tamaño_total += archivo.stat().st_size

                    with open(archivo, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)

                    timestamp = datetime.fromisoformat(cache_data["timestamp"])
                    expiracion = timestamp + timedelta(hours=self.expiration_hours)

                    if datetime.now() > expiracion:
                        expirados += 1

                except Exception:
                    continue

            return {
                "total_archivos": total,
                "archivos_expirados": expirados,
                "archivos_validos": total - expirados,
                "tamaño_total_mb": round(tamaño_total / (1024 * 1024), 2),
                "directorio": str(self.cache_dir)
            }

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}

    def existe(self, identificador: str, check_expiration: bool = True) -> bool:
        """Verifica si existe un elemento en caché"""
        if check_expiration:
            return self.obtener(identificador) is not None
        else:
            clave = self._generar_clave(identificador)
            return self._ruta_archivo(clave).exists()
