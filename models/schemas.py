from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime


class ScrapeRequest(BaseModel):
    """Modelo de request para el endpoint de scraping"""
    site: str = Field(..., description="Identificador del scraper a utilizar (quotes, hackernews, generic)")
    criteria: Dict[str, Any] = Field(
        default_factory=dict,
        description="Criterios/parámetros para el scraping",
        example={
            "url": "https://example.com",
            "selector": "div.content"
        }
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "site": "quotes",
                "criteria": {
                    "url": "http://quotes.toscrape.com",
                    "max_quotes": 5
                }
            }
        }


class ScrapeResponse(BaseModel):
    """Modelo de respuesta para el endpoint de scraping"""
    site: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "site": "quotes",
                "status": "success",
                "data": {
                    "quotes": [
                        {
                            "text": "Example quote",
                            "author": "Author Name",
                            "tags": ["tag1", "tag2"]
                        }
                    ],
                    "count": 1
                },
                "timestamp": "2025-11-25T10:30:00Z"
            }
        }


class ScraperInfo(BaseModel):
    """Información sobre un scraper disponible"""
    site: str
    name: str
    type: str
    description: str


class ScrapersListResponse(BaseModel):
    """Lista de scrapers disponibles"""
    count: int
    scrapers: List[ScraperInfo]


class ErrorResponse(BaseModel):
    """Modelo de respuesta para errores"""
    error: str
    detail: Optional[str] = None
    status: str = "failed"
