from typing import Dict, Any, List, Optional
from scrapers.base_scraper import BaseScraper
from scrapers.example_scrapers import QuotesScraper, HackerNewsScraper, GenericScraper
from scrapers.dontorrent_scraper import DontorrentScraper
from scrapers.dontorrent_fast_scraper import DontorrentFastScraper
from scrapers.btdig_scraper import BtdigScraper
import logging

logger = logging.getLogger(__name__)


class ScraperManager:
    """
    Manejador general de scrapers.
    Gestiona el registro de scrapers y enruta las solicitudes al scraper apropiado.
    """
    
    def __init__(self):
        """Inicializa el manejador y registra los scrapers disponibles"""
        self._scrapers: Dict[str, BaseScraper] = {}
        self._register_default_scrapers()
    
    def _register_default_scrapers(self):
        """Registra los scrapers por defecto"""
        self.register_scraper("quotes", QuotesScraper())
        self.register_scraper("hackernews", HackerNewsScraper())
        self.register_scraper("generic", GenericScraper())
        self.register_scraper("dontorrent", DontorrentScraper())
        ## self.register_scraper("dontorrent-fast", DontorrentFastScraper())
        self.register_scraper("btdig", BtdigScraper())
        logger.info(f"Registered {len(self._scrapers)} default scrapers")
    
    def register_scraper(self, site: str, scraper: BaseScraper) -> None:
        """
        Registra un nuevo scraper.
        
        Args:
            site: Identificador del sitio/scraper
            scraper: Instancia del scraper
        """
        if not isinstance(scraper, BaseScraper):
            raise ValueError(f"Scraper must be an instance of BaseScraper")
        
        self._scrapers[site] = scraper
        logger.info(f"Registered scraper for site: {site}")
    
    def unregister_scraper(self, site: str) -> bool:
        """
        Elimina un scraper registrado.
        
        Args:
            site: Identificador del sitio/scraper
            
        Returns:
            True si se eliminó, False si no existía
        """
        if site in self._scrapers:
            del self._scrapers[site]
            logger.info(f"Unregistered scraper for site: {site}")
            return True
        return False
    
    def get_scraper(self, site: str) -> Optional[BaseScraper]:
        """
        Obtiene un scraper específico.
        
        Args:
            site: Identificador del sitio/scraper
            
        Returns:
            Instancia del scraper o None si no existe
        """
        return self._scrapers.get(site)
    
    def list_available_scrapers(self) -> List[Dict[str, str]]:
        """
        Lista todos los scrapers disponibles.
        
        Returns:
            Lista de diccionarios con información de cada scraper
        """
        return [
            {
                "site": site,
                **scraper.get_info()
            }
            for site, scraper in self._scrapers.items()
        ]
    
    def scrape(self, site: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta el scraping usando el scraper apropiado.
        
        Args:
            site: Identificador del sitio a scrapear
            criteria: Criterios/parámetros para el scraping
            
        Returns:
            Diccionario con los resultados del scraping
        """
        # Verificar si el scraper existe
        scraper = self.get_scraper(site)
        if not scraper:
            available = list(self._scrapers.keys())
            return {
                "error": f"Scraper '{site}' not found",
                "available_scrapers": available,
                "status": "failed"
            }
        
        # Validar criterios
        try:
            if not scraper.validate_criteria(criteria):
                return {
                    "error": f"Invalid criteria for scraper '{site}'",
                    "criteria": criteria,
                    "status": "failed"
                }
        except Exception as e:
            logger.error(f"Error validating criteria for {site}: {str(e)}")
            return {
                "error": f"Validation error: {str(e)}",
                "status": "failed"
            }
        
        # Ejecutar scraping
        try:
            logger.info(f"Starting scrape for site: {site}")
            result = scraper.scrape(criteria)
            
            # Agregar metadatos
            result["status"] = result.get("status", "success" if "error" not in result else "failed")
            result["site"] = site
            
            logger.info(f"Scraping completed for site: {site}")
            return result
            
        except Exception as e:
            logger.error(f"Error during scraping for {site}: {str(e)}")
            return {
                "error": f"Scraping error: {str(e)}",
                "site": site,
                "status": "failed"
            }
    
    def has_scraper(self, site: str) -> bool:
        """
        Verifica si existe un scraper para un sitio.
        
        Args:
            site: Identificador del sitio
            
        Returns:
            True si existe, False en caso contrario
        """
        return site in self._scrapers
    
    def get_scraper_count(self) -> int:
        """
        Obtiene el número de scrapers registrados.
        
        Returns:
            Número de scrapers
        """
        return len(self._scrapers)


# Singleton instance
scraper_manager = ScraperManager()
