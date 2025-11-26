# Ejemplos de uso de la API

Este documento contiene ejemplos prácticos de cómo usar la API.

## 1. Scraper de Quotes

### Request básico
```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "site": "quotes",
    "criteria": {
      "max_quotes": 5
    }
  }'
```

### Response
```json
{
  "site": "quotes",
  "status": "success",
  "data": {
    "quotes": [
      {
        "text": "The world as we have created it...",
        "author": "Albert Einstein",
        "tags": ["change", "deep-thoughts", "thinking"]
      }
    ],
    "count": 5,
    "source": "http://quotes.toscrape.com"
  },
  "timestamp": "2025-11-25T10:30:00Z"
}
```

## 2. Scraper de Hacker News

### Request
```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "site": "hackernews",
    "criteria": {
      "limit": 5
    }
  }'
```

### Python example
```python
import requests

response = requests.post(
    "http://localhost:8000/scrape",
    json={
        "site": "hackernews",
        "criteria": {
            "limit": 10
        }
    }
)

data = response.json()
for story in data["data"]["stories"]:
    print(f"{story['title']}: {story['url']}")
```

## 3. Scraper Genérico

### Extraer títulos H1
```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "site": "generic",
    "criteria": {
      "url": "https://example.com",
      "selector": "h1",
      "extract_text": true
    }
  }'
```

### Extraer enlaces con atributos
```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "site": "generic",
    "criteria": {
      "url": "https://example.com",
      "selector": "a",
      "attributes": ["href", "title"],
      "extract_text": true
    }
  }'
```

## 4. Listar scrapers disponibles

```bash
curl -X GET "http://localhost:8000/sites"
```

### Response
```json
{
  "count": 3,
  "scrapers": [
    {
      "site": "quotes",
      "name": "quotes_toscrape",
      "type": "QuotesScraper",
      "description": "Scraper de ejemplo para http://quotes.toscrape.com"
    },
    {
      "site": "hackernews",
      "name": "hackernews",
      "type": "HackerNewsScraper",
      "description": "Scraper de ejemplo para Hacker News"
    },
    {
      "site": "generic",
      "name": "generic",
      "type": "GenericScraper",
      "description": "Scraper genérico con selectores CSS"
    }
  ]
}
```

## 5. Información de un scraper específico

```bash
curl -X GET "http://localhost:8000/sites/quotes"
```

## 6. Health check

```bash
curl -X GET "http://localhost:8000/health"
```

## Uso con Python

```python
import requests

class ScrapingAPIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def scrape(self, site, criteria):
        response = requests.post(
            f"{self.base_url}/scrape",
            json={"site": site, "criteria": criteria}
        )
        return response.json()
    
    def list_scrapers(self):
        response = requests.get(f"{self.base_url}/sites")
        return response.json()

# Uso
client = ScrapingAPIClient()

# Scrapear quotes
quotes_data = client.scrape("quotes", {"max_quotes": 3})
print(quotes_data)

# Listar scrapers
scrapers = client.list_scrapers()
print(f"Scrapers disponibles: {scrapers['count']}")
```

## Uso con JavaScript/Node.js

```javascript
const axios = require('axios');

async function scrapeQuotes() {
  try {
    const response = await axios.post('http://localhost:8000/scrape', {
      site: 'quotes',
      criteria: {
        max_quotes: 5
      }
    });
    
    console.log(response.data);
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}

scrapeQuotes();
```
