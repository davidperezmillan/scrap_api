from scrapers.base_scraper import BaseScraper
from typing import Dict, Any, List, Optional
import logging
import re
from urllib.parse import unquote

logger = logging.getLogger(__name__)


class BtdigScraper(BaseScraper):
    """
    Scraper para BTDig (btdig.com)
    Busca torrents usando su motor de búsqueda.

    ⚠️ LIMITACIÓN: BTDig tiene protección anti-bot con reCAPTCHA
    que impide el scraping automático. Este scraper puede fallar
    o requerir intervención manual.
    """

    def __init__(self):
        super().__init__(name="btdig")

    def scrape(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Busca torrents en BTDig

        Args:
            criteria: Debe contener:
                - query (str): Término de búsqueda (requerido)
                - max_results (int, optional): Número máximo de resultados (default: 20)

        Returns:
            Dict con los torrents encontrados:
            {
                "torrents": [
                    {
                        "title": "Nombre del torrent",
                        "magnet_link": "magnet:...",
                        "size": "1.49 GB",
                        "files": 4,
                        "age": "found 2 weeks ago",
                        "source": "btdig.com"
                    }
                ],
                "count": 1,
                "query": "término de búsqueda",
                "source": "btdig.com"
            }
        """
        query = criteria.get("query")
        max_results = criteria.get("max_results", 20)

        if not query:
            return {"error": "Se requiere 'query'", "torrents": []}

        logger.info(f"🔍 Buscando '{query}' en BTDig (máx {max_results} resultados)")

        # Construir URL de búsqueda
        search_url = f"https://btdig.com/search?order=0&q={query.replace(' ', '+')}"

        try:
            # Intentar obtener resultados
            html = self.get_html(search_url)
            soup = self.get_soup(search_url)

            if not soup:
                return {
                    "error": "No se pudo acceder a BTDig (posible protección anti-bot)",
                    "torrents": [],
                    "query": query
                }

            # Verificar si hay captcha
            if self._has_captcha(soup):
                logger.warning("⚠️ BTDig requiere verificación captcha")
                return {
                    "error": "BTDig requiere verificación captcha manual",
                    "torrents": [],
                    "query": query,
                    "captcha_required": True
                }

            # Extraer torrents
            torrents = self._extract_torrents(soup, max_results)

            logger.info(f"✅ Encontrados {len(torrents)} torrents en BTDig")

            return {
                "torrents": torrents,
                "count": len(torrents),
                "query": query,
                "source": "btdig.com"
            }

        except Exception as e:
            logger.error(f"Error buscando en BTDig: {e}")
            return {
                "error": str(e),
                "torrents": [],
                "query": query
            }

    def _has_captcha(self, soup) -> bool:
        """Verifica si la página tiene captcha"""
        # Buscar elementos comunes de captcha
        captcha_indicators = [
            soup.find("div", {"id": "g-recaptcha"}),
            soup.find("div", {"class": "captcha"}),
            soup.find(text=re.compile(r"security check", re.IGNORECASE)),
            soup.find(text=re.compile(r"complete the security check", re.IGNORECASE))
        ]

        return any(indicator is not None for indicator in captcha_indicators)

    def _extract_torrents(self, soup, max_results: int) -> List[Dict[str, Any]]:
        """
        Extrae información de torrents de la página de resultados.
        NOTA: Esta implementación es especulativa ya que no podemos
        acceder a resultados reales debido al captcha.
        """
        torrents = []

        # BTDig típicamente muestra resultados en una estructura de tabla o lista
        # Buscar enlaces de magnet o torrent
        magnet_links = soup.find_all("a", href=re.compile(r"magnet:\?"))
        torrent_links = soup.find_all("a", href=re.compile(r"\.torrent$"))

        # Combinar y limitar resultados
        all_links = magnet_links + torrent_links
        all_links = all_links[:max_results]

        for i, link in enumerate(all_links):
            try:
                # Extraer información del torrent
                torrent_data = self._extract_torrent_info(link, soup)
                if torrent_data:
                    torrents.append(torrent_data)

            except Exception as e:
                logger.warning(f"Error extrayendo torrent {i+1}: {e}")
                continue

        return torrents

    def _extract_torrent_info(self, link, soup) -> Optional[Dict[str, Any]]:
        """
        Extrae información detallada de un torrent.
        Busca el título en elementos con clase 'torrent_name'.
        """
        try:
            # El enlace magnet contiene metadatos
            magnet_url = link.get("href")

            # Buscar el contenedor del resultado (div con clase one_result)
            result_container = link.find_parent("div", class_="one_result")
            if not result_container:
                # Si no encontramos one_result, buscar el div torrent_name más cercano
                result_container = link.find_parent("div", class_="torrent_name")
                if result_container:
                    result_container = result_container.find_parent("div")

            # Extraer título del magnet link primero (más confiable)
            title = None
            match = re.search(r'dn=([^&]+)', magnet_url)
            if match:
                title = unquote(match.group(1)).replace('+', ' ')

            # Si no se pudo extraer del magnet, intentar del HTML
            if not title:
                if result_container:
                    torrent_name_div = result_container.find("div", class_="torrent_name")
                    if torrent_name_div:
                        title_link = torrent_name_div.find("a")
                        if title_link:
                            title = self.extract_text(title_link).strip()

            # Si aún no hay título, usar métodos alternativos
            if not title:
                # Buscar en el contenedor del enlace
                container = link.find_parent()
                if container:
                    title_elem = container if container else link
                    title = self.extract_text(title_elem).strip()

                # Si aún no hay título válido, intentar extraer del magnet (fallback)
                if not title or title == magnet_url:
                    match = re.search(r'dn=([^&]+)', magnet_url)
                    if match:
                        title = unquote(match.group(1)).replace('+', ' ')

            # Extraer información adicional del contenedor
            files = None
            size = None
            age = None

            if result_container:
                # Número de archivos
                files_elem = result_container.find("span", class_="torrent_files")
                if files_elem:
                    files_text = self.extract_text(files_elem).strip()
                    try:
                        files = int(files_text)
                    except ValueError:
                        pass

                # Tamaño
                size_elem = result_container.find("span", class_="torrent_size")
                if size_elem:
                    size = self.extract_text(size_elem).strip()

                # Fecha
                age_elem = result_container.find("span", class_="torrent_age")
                if age_elem:
                    age = self.extract_text(age_elem).strip()

            return {
                "title": title,
                "magnet_link": magnet_url,
                "size": size,
                "files": files,
                "age": age,
                "source": "btdig.com"
            }

        except Exception as e:
            logger.error(f"Error extrayendo info del torrent: {e}")
            return None

    def validate_criteria(self, criteria: Dict[str, Any]) -> bool:
        """Valida que se proporcionen los criterios necesarios"""
        return "query" in criteria