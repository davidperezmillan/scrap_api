import re
from typing import List
import requests
from bs4 import BeautifulSoup
from jano.domain.entities.torrent import Torrent
from jano.domain.use_cases.ports import TorrentScrapingService
from jano.infrastructure.external_services.extract_link import get_protected_download_url

import logging
logger = logging.getLogger(__name__)


class DontorrentTorrentScrapingService(TorrentScrapingService):
    """Servicio de scraping complejo para buscar torrents específicos"""


    def search_torrents(self, serie_name: str, start_episode: str, end_episode: str, base_url: str, calidad: str = None, estado: bool = None) -> List[Torrent]:
        """Ejecuta el plugin de scraping complejo para buscar torrents"""
        logger.info(f"Buscando torrents de '{serie_name}' episodios {start_episode}-{end_episode}")

        try:
            # Agrega la URL base a la búsqueda
            search_data = {
                "nombre": serie_name,
                "comienzo": start_episode,
                "fin": end_episode,
                "calidad": calidad or start_episode[0:2],  # Usar calidad proporcionada o extraer de episodio
                "estado": estado,
                "url_parent": base_url
            }

            torrents = []
            series_found = self._get_series(search_data)

            if not series_found:
                logger.info(f"No se encontraron series para '{serie_name}'")
                return torrents

            logger.info(f"Se encontraron {len(series_found)} temporadas")

            # Para cada temporada encontrada, busca los episodios
            for serie_data in series_found:
                episodes = self._get_episodes(serie_data, search_data)
                torrents.extend(episodes)

            # Ordenando los torrents por format descendente
            # 4k > 1080p > 720p > SD
            torrents.sort(key=lambda t: self._get_format_priority(t.format), reverse=True)

            # Eliminar duplicados por status
            unique_torrents = {}
            for torrent in torrents:
                if torrent.status not in unique_torrents:
                    unique_torrents[torrent.status] = torrent
            torrents = list(unique_torrents.values())

            logger.info(f"Se encontraron {len(torrents)} torrents únicos en total")
            return torrents

        except Exception as e:
            logger.error(f"Error en búsqueda de torrents: {e}")
            raise

    def _get_series(self, search_data: dict) -> List[dict]:
        """Busca las series que coinciden con el nombre"""
        serie_name = search_data["nombre"]
        url_parent = search_data["url_parent"]

        logger.info(f"Buscando serie '{serie_name}' en {url_parent}/buscar")

        # Construye la URL de búsqueda
        search_url = f"{url_parent}/buscar"
        data = {"valor": serie_name, "Buscar": "Buscar"}

        logger.info(f"URL de búsqueda: {search_url} con data: {data}")

        req = requests.post(search_url, data=data, timeout=10)
        req.raise_for_status()

        logger.info(f"Respuesta HTTP: {req.status_code}")

        soup = BeautifulSoup(req.text, "html.parser")

        # Busca resultados de series
        series_links = soup.find_all("a", href=re.compile(r"/serie/"))

        logger.info(f"Encontrados {len(series_links)} enlaces potenciales de series")

        series_found = []
        for link in series_links:
            href = link["href"]
            title = link.text.strip()

            logger.info(f"Revisando serie: '{title}' - URL: {href}")

            match_serie, series_name_extracted = self._matches_series_name(title, serie_name)
            # Verifica si el título coincide aproximadamente
            if match_serie:
                logger.info(f"¡Serie coincidente encontrada: '{title}'!")
                series_found.append({
                    "title": series_name_extracted,
                    "title_original": title,
                    "url": f"{url_parent}{href}",
                    "href": href
                })

        logger.info(f"Total de series coincidentes: {len(series_found)}")
        return series_found

    def _matches_series_name(self, title: str, search_name: str) -> bool:
        """Verifica si el título de la serie coincide con la búsqueda"""

        logger.info(f"Comparando título '{title}' con búsqueda '{search_name}'")
        
        # Extrae el nombre de la serie del título encontrado (antes del separador)
        # Ejemplos: "Preacher - 1ª Temporada [720p]" -> "Preacher"
        # "Breaking Bad - Temporada 5" -> "Breaking Bad"
        series_name_from_title = self._extract_series_name_from_title(title)
        
        # Normaliza los nombres para comparación
        title_norm = series_name_from_title.lower().replace(" ", "")
        search_norm = search_name.lower().replace(" ", "")

        # Comparación más precisa para evitar falsos positivos
        # 1. Coincidencia exacta
        if title_norm == search_norm:
            match = True
        # 2. El search_name está al inicio del título encontrado
        elif title_norm.startswith(search_norm):
            match = True
        # 3. El título encontrado está al inicio del search_name
        elif search_norm.startswith(title_norm):
            match = True
        else:
            match = False
        
        logger.info(f"Nombre extraído: '{series_name_from_title}' -> '{title_norm}' vs '{search_norm}' = {match}")
        return match, series_name_from_title
    
    def _extract_series_name_from_title(self, title: str) -> str:
        """Extrae el nombre de la serie del título completo"""
        # Patrones comunes de separación
        separators = [" - ", " – ", " | ", " : ", " temporada ", " season "]
        
        for separator in separators:
            if separator.lower() in title.lower():
                # Toma la parte antes del separador
                parts = title.split(separator, 1)
                if len(parts) > 1:
                    series_name = parts[0].strip()
                    # Limpia caracteres adicionales al final
                    series_name = re.sub(r'[^\w\sÀ-ÿ]', '', series_name).strip()
                    return series_name
        
        # Si no encuentra separador, toma el título completo pero limpia
        return re.sub(r'[^\w\sÀ-ÿ]', '', title).strip()

    def _get_episodes(self, serie_data: dict, search_data: dict) -> List[Torrent]:
        """Obtiene los episodios de una temporada específica"""
        url_parent = search_data["url_parent"]
        start_episode = search_data["comienzo"]
        end_episode = search_data["fin"]

        try:
            logger.info(f"Obteniendo episodios de {serie_data['url']}")

            req = requests.get(serie_data["url"], timeout=10)
            req.raise_for_status()

            soup = BeautifulSoup(req.text, "html.parser")


            # recuperar las filas de la tabla de episodios, que es la unica tabla que hay en la pagina
            tabla = soup.find("table")
            if not tabla:
                logger.warning(f"No se encontró la tabla de episodios en {serie_data['url']}")
                return []
            
            ## recuperamos las filas de la tabla del tbody
            filas = tabla.find("tbody").find_all("tr")
            if not filas or len(filas) < 2:
                logger.warning(f"No se encontraron filas de episodios en la tabla de {serie_data['url']}")
                return []

            torrents = []
            # recorremos las filas para encontrar los enlaces de los episodios
            episode_links = []
            for fila in filas:
                ## la primera columna es el capitulo, la segunda columna es el enlace
                columnas = fila.find_all("td")

                ## recuperamos el formato
                episode_format, format_string_original = self._extract_series_format_category(soup)
                # extraer el codigo de episodio de la primera columna
                episode_code = self._extract_episode_code(columnas[0].text.strip())
                episode_code = f"{episode_format}{episode_code}"
                if not episode_code:
                    logger.info(f"No se pudo extraer el código de episodio de la fila: {fila}")
                    continue




                ##quality = "HD" if re.search(r"(\d{3,4}p)", episode_title) else "SD"
                status = f"{episode_code}"
                # Verificar que el status tenga el formato correcto (HDS01E02 o SDS99E99)
                if not self._is_valid_status_format(status):
                    logger.warning(f"Formato de status inválido: '{status}', omitiendo episodio")
                    continue
                ############## ATENCIÓN AQUI ##############
                ## Revisamos si esta en rango, para evitar llamadas innecesarias a get_protected_download_url
                if (not self._is_in_range(episode_code, start_episode, end_episode)):
                    logger.warning(f"Episodio fuera de rango: {episode_code}, omitiendo")
                    continue
              

                if len(columnas) < 2:
                    logger.warning(f"Fila con formato inesperado, omitiendo: {fila}")
                    continue
                ## recuperqar data_content_id si existe
                enlace = columnas[1].find("a")
                content_id = enlace.get("data-content-id")  # Devuelve None si no existe
                data_tabla = enlace.get("data-tabla")
                protected_url = get_protected_download_url(content_id, "series", url_parent)
                protected_url = f"{url_parent}{protected_url}"



                torrent = Torrent(
                    status=status,
                    format=format_string_original,
                    title=serie_data["title"],
                    title_original=serie_data["title_original"],
                    link=protected_url,
                    episode_code=episode_code
                )
                torrents.append(torrent)

            logger.info(f"Se encontraron {len(torrents)} torrents en la temporada '{serie_data['title']}'")

                        # Ordenando los torrents por format descendente
            # 4k > 1080p > 720p > SD
            torrents.sort(key=lambda t: self._get_format_priority(t.format), reverse=True)

            # Eliminar duplicados por status
            unique_torrents = {}
            for torrent in torrents:
                if torrent.status not in unique_torrents:
                    unique_torrents[torrent.status] = torrent
            torrents = list(unique_torrents.values())
            logger.info(f"Se encontraron {len(torrents)} torrents únicos en la temporada '{serie_data['title']}'")


            return torrents

        except Exception as e:
            logger.error(f"Error obteniendo episodios de {serie_data['url']}: {e}")
            return []

    def _extract_episode_code(self, title: str) -> str:
        """Extrae el código de episodio del título"""
        # Busca patrones como S01E01, 1x01, etc.
        patterns = [
            r'S(\d{1,2})E(\d{1,3})',  # S01E01
            r'(\d{1,2})x(\d{1,3})',   # 1x01
        ]
        logger.info(f"Extrayendo código de episodio de título: '{title}'")
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                if 'S' in pattern:
                    season = match.group(1).zfill(2)
                    episode = match.group(2).zfill(2)
                    return f"S{season}E{episode}"
                else:
                    season = match.group(1).zfill(2)
                    episode = match.group(2).zfill(2)
                    return f"S{season}E{episode}"

        return None

    def _is_in_range(self, episode_code: str, start: str, end: str) -> bool:
        """Verifica si un episodio está dentro del rango especificado"""
        try:
            # Convierte a números para comparación
            ep_num = self._episode_to_number(episode_code)
            start_num = self._episode_to_number(start)
            end_num = self._episode_to_number(end)

            return start_num <= ep_num <= end_num
        except:
            return False

    def _episode_to_number(self, episode_code: str) -> int:
        """Convierte un código de episodio a número para comparación"""
        if "S" in episode_code and "E" in episode_code:
            season = int(episode_code.split("S")[1].split("E")[0])
            episode = int(episode_code.split("E")[1])
            return season * 1000 + episode  # Temporada * 1000 + episodio
        return 0

    def _is_valid_status_format(self, status: str) -> bool:
        """Verifica que el status tenga el formato correcto: HDS01E02 o SDS99E99"""
        pattern = r'^(HD|SD)S\d{2}E\d{2}$'
        return bool(re.match(pattern, status))

    def _extract_series_format_category(self, soup: BeautifulSoup) -> str:
        
        format_string = self._extract_series_format(soup)
        logger.info(f"Formato extraído: {format_string}")
        # Determina la categoría de calidad basada en el formato extraído
        # puede ser 720p, 1080p, 4K, todo lo demas sera SD
        if "4K" in format_string:
            return "HD", format_string
        match = re.search(r"(\d{3,4})p", format_string)
        if match:
            resolution = int(match.group(1))
            if resolution >= 720:
                return "HD", format_string
        return "SD", format_string


    def _extract_series_format(self, soup: BeautifulSoup) -> str:
        """
        Extrae el formato de la serie desde el HTML de la página.
        Determinación de calidad: Basado en el formato extraído, 
        si contiene "4K" o un número >= 720 (como 720p, 1080p, etc.), se clasifica como "HD"; de lo contrario, "SD".
        
        Args:
            soup: El objeto BeautifulSoup del contenido HTML de la página de la serie.
        
        Returns:
            El formato extraído (ej. '720p', '1080p', '4K', etc.) o 'Unknown' si no se encuentra.
        """
        
        # Método 1: Extraer del título de la página (title tag)
        title_tag = soup.find("title")
        if title_tag:
            title_text = title_tag.text
            match = re.search(r"\[(\d{3,4}p|4K)\]", title_text)
            if match:
                return match.group(1)
        
        # Método 2: Extraer del encabezado H2 con clase 'descargarTitulo'
        h2_tag = soup.find("h2", class_="descargarTitulo")
        if h2_tag:
            h2_text = h2_tag.text
            match = re.search(r"\[(\d{3,4}p|4K)\]", h2_text)
            if match:
                return match.group(1)
        
        # Método 3: Extraer del párrafo que contiene "Formato:"
        formato_p = soup.find("p", string=re.compile(r"Formato:"))
        if formato_p:
            formato_text = formato_p.text
            match = re.search(r"Formato:\s*([^\s<]+)", formato_text)
            if match:
                formato_full = match.group(1)  # ej. "HDTV-720p"
                # Extraer el número de resolución o 4K
                res_match = re.search(r"(\d{3,4}p|4K)", formato_full)
                if res_match:
                    return res_match.group(1)
        
        # Método 4: Extraer de los nombres de archivos de torrent (como fallback)
        torrent_links = soup.find_all("a", href=re.compile(r"\.torrent$"))
        for link in torrent_links:
            href = link['href']
            match = re.search(r"(\d{3,4}p|4K)", href)
            if match:
                return match.group(1)
        
        return "Unknown"


    def _extract_content_id(self, href: str) -> str:
        """Extrae el content_id del href del enlace torrent"""
        # Asume que href contiene un número, como /download/123.torrent
        match = re.search(r'/(\d+)\.torrent', href)
        if match:
            return match.group(1)
        return None


    def _get_format_priority(self, format_str: str) -> int:
        """Asigna prioridad al formato: 4K > 1080p > 720p > SD"""
        logger.info(f"Obteniendo prioridad para el formato: {format_str}")
        if "720p" in format_str:
            return 4
        elif "1080p" in format_str:
            return 3
        elif "4K" in format_str:
            return 2
        elif format_str == "SD":
            return 1
        else:
            return 0