# API de Web Scraping Modular

API RESTful para realizar scraping de múltiples páginas web de forma modular y extensible.

## 🚀 Características

- **Arquitectura modular**: Fácil agregar nuevos scrapers para diferentes páginas
- **API RESTful**: Endpoints documentados con FastAPI
- **Gestión centralizada**: Manejador general que enruta a scrapers específicos
- **Extensible**: Clase base para crear nuevos scrapers rápidamente
- **Ordenamiento inteligente**: Resultados ordenados por preferencia (720p > 1080p > 4K > SD)
- **Dos versiones de scrapers**: Completo (con alternativas) y Rápido (solo mejores opciones)
- **Optimizado para performance**: Versión rápida hasta 73% más veloz

## 📁 Estructura del Proyecto

```
scrap_api/
├── api/
│   ├── __init__.py
│   └── routes.py          # Endpoints de la API
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py    # Clase base abstracta
│   ├── example_scraper.py # Ejemplo de scraper
│   ├── dontorrent_scraper.py # Scraper de torrents (completo)
│   ├── dontorrent_fast_scraper.py # Scraper optimizado (rápido)
│   └── manager.py         # Manejador general
├── models/
│   ├── __init__.py
│   └── schemas.py         # Modelos Pydantic
├── utils/
│   ├── __init__.py
│   └── helpers.py         # Utilidades comunes
├── docs/
│   └── reference/         # Código original de referencia
├── main.py                # Punto de entrada
├── config.py              # Configuración
├── requirements.txt
└── README.md
```

## 🛠️ Instalación

1. Crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno (opcional):
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

## 🏃 Uso

1. Iniciar el servidor:
```bash
python main.py
```

O con uvicorn directamente:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. Acceder a la documentación interactiva:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📝 Endpoints

### GET /
Información general de la API

### POST /scrape
Realizar scraping de una página

**Request Body:**
```json
{
  "site": "example",
  "criteria": {
    "url": "https://example.com",
    "selector": "div.content"
  }
}
```

**Response:**
```json
{
  "site": "example",
  "data": [...],
  "timestamp": "2025-11-25T10:30:00Z",
  "status": "success"
}
```

### GET /sites
Listar todos los scrapers disponibles

## 🎯 Scrapers Disponibles

### 1. Dontorrent (Completo) - `dontorrent`
- **Uso**: Interfaces interactivas, cuando necesitas ver todas las opciones
- **Devuelve**: Mejores torrents + alternativas disponibles
- **Performance**: ~5-10 segundos para una temporada
- **Documentación**: [DONTORRENT_GUIDE.md](./DONTORRENT_GUIDE.md)

### 2. Dontorrent Fast - `dontorrent-fast` ⚡
- **Uso**: Automatizaciones, scripts, descargas masivas
- **Devuelve**: Solo los mejores torrents (sin alternativas)
- **Performance**: ~1-3 segundos para una temporada (73% más rápido)
- **Documentación**: [DONTORRENT_GUIDE.md](./DONTORRENT_GUIDE.md)

**Ejemplo de uso:**

```bash
# Versión completa (con alternativas)
curl -X POST http://localhost:7002/scrape -H "Content-Type: application/json" -d '{
  "site": "dontorrent",
  "criteria": {
    "serie_name": "Breaking Bad",
    "start_episode": "S01E01",
    "end_episode": "S01E10",
    "base_url": "https://dontorrent.monster"
  }
}'

# Versión rápida (solo mejores) ⚡
curl -X POST http://localhost:7002/scrape -H "Content-Type: application/json" -d '{
  "site": "dontorrent-fast",
  "criteria": {
    "serie_name": "Breaking Bad",
    "start_episode": "S01E01",
    "end_episode": "S01E10",
    "base_url": "https://dontorrent.monster"
  }
}'
```

## 🔧 Agregar un Nuevo Scraper

1. Crear un nuevo archivo en `scrapers/`:

```python
from scrapers.base_scraper import BaseScraper
from typing import Dict, Any

class MiNuevoScraper(BaseScraper):
    def __init__(self):
        super().__init__(name="mi_sitio")
    
    def scrape(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        url = criteria.get("url")
        # Tu lógica de scraping aquí
        soup = self.get_soup(url)
        data = soup.find_all("div", class_="item")
        
        return {
            "items": [item.text for item in data],
            "count": len(data)
        }
    
    def validate_criteria(self, criteria: Dict[str, Any]) -> bool:
        return "url" in criteria
```

2. Registrar el scraper en `scrapers/manager.py`:

```python
from scrapers.mi_nuevo_scraper import MiNuevoScraper

# En el __init__ de ScraperManager:
self.register_scraper("mi_sitio", MiNuevoScraper())
```

## 🐳 Docker (Opcional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📄 Licencia

MIT
