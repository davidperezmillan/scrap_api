from scrapers.base_scraper import BaseScraper
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class QuotesScraper(BaseScraper):
    """
    Scraper de ejemplo para http://quotes.toscrape.com
    Extrae citas famosas, autores y tags.
    """

    def __init__(self):
        super().__init__(name="quotes_toscrape")

    def scrape(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scrapea citas de quotes.toscrape.com

        Args:
            criteria: Debe contener:
                - url: URL de la página (opcional, usa default)
                - max_quotes: Número máximo de citas a extraer (opcional)

        Returns:
            Dict con las citas extraídas
        """
        url = criteria.get("url", "http://quotes.toscrape.com")
        max_quotes = criteria.get("max_quotes", 10)

        soup = self.get_soup(url)
        if not soup:
            return {"error": "No se pudo obtener la página", "quotes": []}

        quotes_elements = soup.find_all("div", class_="quote", limit=max_quotes)
        quotes = []

        for quote_elem in quotes_elements:
            quote_data = {
                "text": self.extract_text(quote_elem.find("span", class_="text")),
                "author": self.extract_text(quote_elem.find("small", class_="author")),
                "tags": [self.extract_text(tag) for tag in quote_elem.find_all("a", class_="tag")]
            }
            quotes.append(quote_data)

        return {
            "quotes": quotes,
            "count": len(quotes),
            "source": url
        }

    def validate_criteria(self, criteria: Dict[str, Any]) -> bool:
        """Valida que se proporcionen los criterios necesarios"""
        return "url" in criteria


class HackerNewsScraper(BaseScraper):
    """
    Scraper de ejemplo para Hacker News (news.ycombinator.com)
    Extrae las historias principales con puntos, comentarios y enlaces.
    """

    def __init__(self):
        super().__init__(name="hackernews")

    def scrape(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scrapea historias de Hacker News

        Args:
            criteria: Debe contener:
                - max_stories: Número máximo de historias a extraer (opcional)

        Returns:
            Dict con las historias extraídas
        """
        url = "https://news.ycombinator.com/"
        max_stories = criteria.get("max_stories", 10)

        soup = self.get_soup(url)
        if not soup:
            return {"error": "No se pudo obtener la página", "stories": []}

        # Encontrar las filas de historias (clase 'athing')
        story_rows = soup.find_all("tr", class_="athing", limit=max_stories)
        stories = []

        for row in story_rows:
            title_elem = row.find("a", class_="titlelink")
            if not title_elem:
                continue

            # Obtener el ID de la historia para buscar más info
            story_id = row.get("id")

            # Buscar la fila siguiente con info adicional
            subtext_row = row.find_next_sibling("tr")
            subtext = subtext_row.find("td", class_="subtext") if subtext_row else None

            story_data = {
                "id": story_id,
                "title": self.extract_text(title_elem),
                "url": title_elem.get("href"),
                "score": self._extract_score(subtext),
                "comments": self._extract_comments(subtext),
                "author": self._extract_author(subtext)
            }
            stories.append(story_data)

        return {
            "stories": stories,
            "count": len(stories),
            "source": url
        }

    def _extract_score(self, subtext_elem):
        """Extrae el puntaje de una historia"""
        if not subtext_elem:
            return 0
        score_elem = subtext_elem.find("span", class_="score")
        if score_elem:
            score_text = self.extract_text(score_elem)
            # "123 points" -> 123
            import re
            match = re.search(r'(\d+)', score_text)
            return int(match.group(1)) if match else 0
        return 0

    def _extract_comments(self, subtext_elem):
        """Extrae el número de comentarios"""
        if not subtext_elem:
            return 0
        # Buscar enlaces que contengan "comments" o "comment"
        comment_links = subtext_elem.find_all("a", string=lambda text: text and ("comment" in text.lower()))
        if comment_links:
            comment_text = self.extract_text(comment_links[0])
            import re
            match = re.search(r'(\d+)', comment_text)
            return int(match.group(1)) if match else 0
        return 0

    def _extract_author(self, subtext_elem):
        """Extrae el autor de la historia"""
        if not subtext_elem:
            return None
        author_elem = subtext_elem.find("a", class_="hnuser")
        return self.extract_text(author_elem) if author_elem else None

    def validate_criteria(self, criteria: Dict[str, Any]) -> bool:
        """Valida que se proporcionen los criterios necesarios"""
        return True  # No requiere criterios específicos


class GenericScraper(BaseScraper):
    """
    Scraper genérico que puede extraer datos básicos de cualquier sitio web.
    Útil para prototipado rápido o sitios simples.
    """

    def __init__(self):
        super().__init__(name="generic")

    def scrape(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scrapea datos genéricos de una URL

        Args:
            criteria: Debe contener:
                - url: URL de la página a scrapear (requerido)
                - selectors: Dict con selectores CSS para extraer datos (opcional)
                  Ejemplo: {"title": "h1", "links": "a", "images": "img"}

        Returns:
            Dict con los datos extraídos
        """
        url = criteria.get("url")
        selectors = criteria.get("selectors", {})

        if not url:
            return {"error": "Se requiere 'url'", "data": {}}

        soup = self.get_soup(url)
        if not soup:
            return {"error": "No se pudo obtener la página", "data": {}}

        data = {}

        # Extraer datos usando selectores personalizados
        for key, selector in selectors.items():
            elements = soup.select(selector)
            if len(elements) == 1:
                # Si hay un solo elemento, devolver el texto
                data[key] = self.extract_text(elements[0])
            elif len(elements) > 1:
                # Si hay múltiples elementos, devolver lista de textos
                data[key] = [self.extract_text(elem) for elem in elements]
            else:
                data[key] = None

        # Datos básicos por defecto si no se especifican selectores
        if not selectors:
            data.update({
                "title": self.extract_text(soup.find("title")),
                "h1": [self.extract_text(h1) for h1 in soup.find_all("h1")],
                "links": len(soup.find_all("a")),
                "images": len(soup.find_all("img")),
                "paragraphs": len(soup.find_all("p"))
            })

        return {
            "data": data,
            "source": url,
            "selectors_used": list(selectors.keys()) if selectors else "default"
        }

    def validate_criteria(self, criteria: Dict[str, Any]) -> bool:
        """Valida que se proporcionen los criterios necesarios"""
        return "url" in criteria