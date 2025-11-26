# Archivos de Referencia

Esta carpeta contiene los archivos originales que sirvieron de base para crear el scraper `dontorrent`.

## 📄 Archivos

### `extract_link.py`
Implementación original del sistema de **Proof of Work (PoW)** para obtener URLs de descarga protegidas.

**Funciones principales:**
- `compute_proof_of_work()` - Calcula el nonce necesario para resolver el challenge
- `get_protected_download_url()` - Obtiene la URL de descarga haciendo las llamadas al servidor

**Uso en el proyecto:**
Este código fue integrado directamente en `scrapers/dontorrent_scraper.py` en el método `_get_protected_download_url()`.

### `torrent_scraping_service.py`
Servicio original de scraping de torrents para Dontorrent.

**Características implementadas:**
- Búsqueda de series por nombre
- Extracción de episodios con filtrado por rango
- Detección automática de formato (720p, 1080p, 4K, SD)
- Normalización de códigos de episodio
- Ordenamiento por prioridad de formato

**Uso en el proyecto:**
La lógica de este archivo fue adaptada y modularizada en `scrapers/dontorrent_scraper.py`, siguiendo la arquitectura de la API con `BaseScraper`.

## 🔄 Diferencias con la Implementación Actual

### Dependencias Eliminadas
Los archivos originales dependían de:
```python
from jano.domain.entities.torrent import Torrent
from jano.domain.use_cases.ports import TorrentScrapingService
```

La implementación actual es **autónoma** y no requiere dependencias externas específicas del framework Jano.

### Mejoras Implementadas
1. **Sistema de dos listas**: `torrents` y `torrents_rest`
2. **Normalización robusta de formatos**: Solo formatos válidos (720p, 1080p, 4K, SD)
3. **Orden de prioridad ajustable**: 720p > 1080p > 4K > SD
4. **Integración con FastAPI**: Endpoints RESTful documentados
5. **Logging mejorado**: Trazabilidad completa del proceso
6. **Validación de formatos**: No se muestran formatos "Unknown" o inválidos

## 📚 Referencias

Estos archivos se mantienen como referencia histórica y documentación del diseño original.

**Para el código actual en producción**, consulta:
- `scrapers/dontorrent_scraper.py`
- `DONTORRENT_GUIDE.md` (documentación consolidada)
