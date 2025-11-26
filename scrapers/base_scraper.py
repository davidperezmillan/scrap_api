from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Clase base abstracta para todos los scrapers.
    Proporciona funcionalidad común y define la interfaz que deben implementar
    los scrapers específicos.
    """
    
    def __init__(self, name: str):
        """
        Inicializa el scraper base.
        
        Args:
            name: Nombre identificador del scraper
        """
        self.name = name
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = 30
        
    @abstractmethod
    def scrape(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Método principal de scraping. Debe ser implementado por cada scraper específico.
        
        Args:
            criteria: Diccionario con los criterios de búsqueda/scraping
                     Ejemplo: {"url": "https://...", "selector": "div.content", ...}
        
        Returns:
            Diccionario con los datos extraídos
        """
        pass
    
    @abstractmethod
    def validate_criteria(self, criteria: Dict[str, Any]) -> bool:
        """
        Valida que los criterios proporcionados sean correctos para este scraper.
        
        Args:
            criteria: Diccionario con los criterios a validar
            
        Returns:
            True si los criterios son válidos, False en caso contrario
        """
        pass
    
    def get_soup(self, url: str, parser: str = 'html.parser') -> Optional[BeautifulSoup]:
        """
        Obtiene un objeto BeautifulSoup desde una URL.
        
        Args:
            url: URL a scrapear
            parser: Parser a utilizar (html.parser, lxml, etc.)
            
        Returns:
            Objeto BeautifulSoup o None si hay error
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, parser)
        except requests.RequestException as e:
            logger.error(f"Error al obtener URL {url}: {str(e)}")
            return None
    
    def get_html(self, url: str) -> Optional[str]:
        """
        Obtiene el HTML de una URL como string.
        
        Args:
            url: URL a obtener
            
        Returns:
            HTML como string o None si hay error
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error al obtener HTML de {url}: {str(e)}")
            return None
    
    def extract_text(self, element) -> str:
        """
        Extrae texto de un elemento BeautifulSoup, limpiando espacios.
        
        Args:
            element: Elemento BeautifulSoup
            
        Returns:
            Texto limpio
        """
        if element:
            return element.get_text(strip=True)
        return ""
    
    def extract_attribute(self, element, attribute: str, default: str = "") -> str:
        """
        Extrae un atributo de un elemento BeautifulSoup.
        
        Args:
            element: Elemento BeautifulSoup
            attribute: Nombre del atributo
            default: Valor por defecto si no existe
            
        Returns:
            Valor del atributo o default
        """
        if element and element.has_attr(attribute):
            return element[attribute]
        return default
    
    def get_info(self) -> Dict[str, str]:
        """
        Retorna información sobre el scraper.
        
        Returns:
            Diccionario con información del scraper
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "description": self.__doc__.strip() if self.__doc__ else "No description"
        }
