# Auditel v3.0 🚀

**Auditel** es un sistema inteligente de análisis normativo para fiscalización pública, con **web scraping funcional** que extrae normativas actualizadas de fuentes oficiales.

## ✨ Características Principales

### 🌐 Web Scraping Funcional
- **Extracción automática** de normativas del DOF y Periódico Oficial de Tlaxcala
- **Búsqueda en tiempo real** de leyes, decretos y acuerdos
- **Caché inteligente** con expiración de 24 horas
- **Búsqueda paralela** en múltiples fuentes simultáneamente

### 🔍 Búsqueda Híbrida Inteligente
- Combina datos locales (JSON) con web scraping
- Motor TF-IDF con similitud de coseno
- Extracción automática de referencias legales
- Procesamiento avanzado de texto

### 🏗️ Arquitectura Modular
- Código organizado en módulos especializados
- Fácil mantenimiento y extensión
- Scrapers extensibles para nuevas fuentes
- Sistema de caché persistente

### 📊 API REST Completa
- Endpoints para consultas normativas
- Gestión de caché
- Pruebas de web scraping
- Estadísticas del sistema

## 🎯 Fuentes de Datos

### Fuentes Locales
- Base de datos JSON de Obra Pública
- Base de datos JSON Financiera

### Fuentes Web (Scraping Activo)
- ✅ [Diario Oficial de la Federación (DOF)](https://www.dof.gob.mx/)
- ✅ [Periódico Oficial del Estado de Tlaxcala](https://periodico.tlaxcala.gob.mx/)
- 🔜 Cámara de Diputados (próximamente)
- 🔜 Suprema Corte de Justicia (próximamente)

## 🚀 Instalación y Uso

### 1. Clonar repositorio

```bash
git clone https://github.com/tu-usuario/auditel.git
cd auditel
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux / macOS
venv\Scripts\activate     # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno (opcional)

```bash
cp .env.example .env
# Editar .env con tu configuración
```

### 5. Ejecutar pruebas

```bash
python test_scraping.py
```

### 6. Iniciar aplicación

```bash
# Versión mejorada con web scraping
python app_v2.py

# O usar el original (sin web scraping)
python app.py
```

La aplicación estará disponible en: `http://localhost:5020`

## 📁 Estructura del Proyecto

```
Auditel-/
├── app_v2.py                 # ✨ Aplicación mejorada con web scraping
├── app.py                    # Aplicación original (respaldo)
├── test_scraping.py          # Script de pruebas
│
├── config/                   # Configuración
│   └── settings.py
│
├── scrapers/                 # Módulos de web scraping
│   ├── base_scraper.py
│   ├── dof_scraper.py
│   ├── tlaxcala_scraper.py
│   └── scraper_manager.py
│
├── models/                   # Modelos de datos
│   └── normativa.py
│
├── utils/                    # Utilidades
│   ├── cache_manager.py
│   └── text_processor.py
│
├── data/                     # Datos JSON
├── cache_data/               # Caché de web scraping
├── logs/                     # Archivos de log
└── templates/                # HTML templates
```

## 🔧 API Endpoints

### Consultas Normativas

```bash
POST /ask
{
  "question": "licitaciones obras públicas",
  "auditoria": "Obra Pública",
  "ente": "Municipal",
  "usar_web_scraping": "true"  # Activar web scraping
}
```

### Estado del Sistema

```bash
GET /health
```

### Gestión de Caché

```bash
# Ver estadísticas
GET /cache/stats

# Limpiar caché
POST /cache/clear
```

### Prueba de Web Scraping

```bash
POST /scraping/test
{
  "query": "obras públicas",
  "fuente": "all"  # o "dof", "tlaxcala"
}
```

## 🧪 Pruebas

```bash
# Ejecutar todas las pruebas
python test_scraping.py

# Pruebas individuales
python -c "from utils.text_processor import TextProcessor; tp = TextProcessor(); print(tp.sanitizar_html('<p>Test</p>'))"
```

## 📖 Documentación Completa

Ver [MEJORAS.md](MEJORAS.md) para:
- Detalles de implementación
- Guía de uso avanzado
- Comparación antes/después
- Posibles expansiones futuras

## 🛠️ Configuración

Edita `config/settings.py` para ajustar:
- Timeouts de scraping
- Expiración de caché
- URLs de fuentes
- Límites de búsqueda
- Y más...

## 🐛 Solución de Problemas

### El web scraping no funciona
- Verificar conectividad a internet
- Revisar logs en `logs/auditel.log`
- Los sitios web pueden haber cambiado estructura

### Caché no se guarda
- Verificar permisos en directorio `cache_data/`
- Revisar espacio en disco

### Errores de importación
- Asegurar que todas las dependencias están instaladas
- Ejecutar `pip install -r requirements.txt`

## 📊 Características v3.0

✅ Web scraping funcional de fuentes oficiales
✅ Búsqueda híbrida (local + web)
✅ Caché inteligente con persistencia
✅ Procesamiento avanzado de texto
✅ Extracción de referencias legales
✅ Arquitectura modular escalable
✅ API REST completa
✅ Sistema de pruebas incluido
✅ Logging estructurado
✅ Manejo robusto de errores

## 🔮 Próximas Funcionalidades

- [ ] Más fuentes de scraping (Cámara de Diputados, SCJN)
- [ ] Base de datos SQL para mejor rendimiento
- [ ] Integración con OpenAI para análisis profundo
- [ ] Dashboard con estadísticas
- [ ] Alertas de nuevas normativas
- [ ] Exportación a PDF/Word
- [ ] API GraphQL

## 📝 Licencia

[Especificar licencia]

## 👥 Contribuir

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📞 Soporte

Para problemas o sugerencias, abrir un issue en GitHub

