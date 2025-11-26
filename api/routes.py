from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from models.schemas import (
    ScrapeRequest,
    ScrapeResponse,
    ScrapersListResponse,
    ScraperInfo,
    ErrorResponse
)
from scrapers.manager import scraper_manager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", tags=["General"])
async def root():
    """
    Endpoint raíz - Información general de la API
    """
    return {
        "name": "Web Scraping API",
        "version": "1.0.0",
        "description": "API modular para scraping de múltiples sitios web",
        "endpoints": {
            "scrape": "/scrape (POST)",
            "list_scrapers": "/sites (GET)",
            "scraper_info": "/sites/{site} (GET)",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@router.get("/sites", response_model=ScrapersListResponse, tags=["Scrapers"])
async def list_scrapers():
    """
    Lista todos los scrapers disponibles
    
    Returns:
        Lista de scrapers con su información
    """
    scrapers = scraper_manager.list_available_scrapers()
    return {
        "count": len(scrapers),
        "scrapers": scrapers
    }


@router.get("/sites/{site}", response_model=ScraperInfo, tags=["Scrapers"])
async def get_scraper_info(site: str):
    """
    Obtiene información sobre un scraper específico
    
    Args:
        site: Identificador del scraper
        
    Returns:
        Información del scraper
    """
    scraper = scraper_manager.get_scraper(site)
    if not scraper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scraper '{site}' not found"
        )
    
    info = scraper.get_info()
    return {
        "site": site,
        **info
    }


@router.post("/scrape", tags=["Scraping"])
async def scrape_site(request: ScrapeRequest):
    """
    Realiza scraping de un sitio web
    
    Args:
        request: Solicitud con el sitio y criterios de scraping
        
    Returns:
        Datos extraídos del sitio web
        
    Example request:
        ```json
        {
            "site": "quotes",
            "criteria": {
                "url": "http://quotes.toscrape.com",
                "max_quotes": 5
            }
        }
        ```
    
    Example request (generic):
        ```json
        {
            "site": "generic",
            "criteria": {
                "url": "https://example.com",
                "selector": "h1",
                "extract_text": true
            }
        }
        ```
    """
    logger.info(f"Received scrape request for site: {request.site}")
    
    # Ejecutar scraping
    result = scraper_manager.scrape(request.site, request.criteria)
    
    # Si hay error, retornar con código 400
    if result.get("status") == "failed":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "site": request.site,
                "status": "failed",
                "error": result.get("error", "Unknown error"),
                "timestamp": datetime.now().isoformat()
            }
        )
    
    # Retornar resultado exitoso
    return {
        "site": request.site,
        "status": result.get("status", "success"),
        "data": result,
        "timestamp": datetime.now()
    }


@router.get("/health", tags=["General"])
async def health_check():
    """
    Endpoint de salud para verificar que la API está funcionando
    """
    return {
        "status": "healthy",
        "scrapers_loaded": scraper_manager.get_scraper_count(),
        "timestamp": datetime.now()
    }
