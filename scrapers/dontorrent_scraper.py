from scrapers.base_scraper import BaseScraper
from typing import Dict, Any, List
import requests
from bs4 import BeautifulSoup
import re
import hashlib
import time
import logging

logger = logging.getLogger(__name__)


class DontorrentScraper(BaseScraper):
    """
    Scraper para sitios de torrents con protección PoW (Proof of Work).
    Busca series/torrents y obtiene enlaces de descarga protegidos.
    """
    
    def __init__(self):
        super().__init__(name="dontorrent")
        
    def scrape(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scrapea torrents de series
        
        Args:
            criteria: Debe contener:
                - base_url: URL base del sitio (requerido)
                - serie_name: Nombre de la serie (requerido)
                - start_episode: Episodio inicial (formato: S01E01 o HDS01E01)
                - end_episode: Episodio final (formato: S01E01 o HDS01E01)
                - calidad: Calidad deseada (opcional: HD, SD)
        
        Returns:
            Dict con los torrents encontrados
        """
        base_url = criteria.get("base_url")
        serie_name = criteria.get("serie_name")
        start_episode = criteria.get("start_episode")
        end_episode = criteria.get("end_episode")
        calidad = criteria.get("calidad")
        
        if not all([base_url, serie_name, start_episode, end_episode]):
            return {
                "error": "Faltan parámetros requeridos: base_url, serie_name, start_episode, end_episode",
                "torrents": []
            }
        
        try:
            logger.info(f"Buscando torrents de '{serie_name}' episodios {start_episode}-{end_episode}")
            
            # 1. Buscar series que coincidan
            series_found = self._search_series(base_url, serie_name)
            
            if not series_found:
                return {
                    "message": f"No se encontraron series para '{serie_name}'",
                    "torrents": [],
                    "count": 0
                }
            
            logger.info(f"Se encontraron {len(series_found)} temporadas")
            
            # 2. Obtener episodios de cada temporada
            all_torrents = []
            for serie_data in series_found:
                episodes = self._get_episodes(
                    serie_data, 
                    base_url, 
                    start_episode, 
                    end_episode,
                    calidad
                )
                all_torrents.extend(episodes)
            
            # 3. Ordenar por prioridad (720p > 1080p > 4K > SD)
            all_torrents.sort(key=lambda t: self._get_format_priority(t.get("format", "")), reverse=True)
            
            # 4. Separar en torrents filtrados y resto
            # Torrents filtrados: el de mayor prioridad por episodio
            unique_torrents = {}
            rest_torrents = []
            
            for torrent in all_torrents:
                status = torrent["status"]
                if status not in unique_torrents:
                    # Primer torrent de este episodio (el de mayor prioridad)
                    unique_torrents[status] = torrent
                else:
                    # Duplicado con menor prioridad
                    rest_torrents.append(torrent)
            
            filtered_torrents = list(unique_torrents.values())
            
            logger.info(f"Torrents filtrados: {len(filtered_torrents)}, resto: {len(rest_torrents)}")
            
            return {
                "torrents": filtered_torrents,  # Lista principal (mayor prioridad)
                "torrents_rest": rest_torrents, # Resto de opciones
                "count": len(filtered_torrents),
                "count_total": len(all_torrents),
                "count_rest": len(rest_torrents),
                "serie_name": serie_name,
                "source": base_url
            }
            
        except Exception as e:
            logger.error(f"Error en búsqueda de torrents: {e}")
            return {
                "error": str(e),
                "torrents": [],
                "count": 0
            }
    
    def validate_criteria(self, criteria: Dict[str, Any]) -> bool:
        """Valida que se proporcionen los criterios necesarios"""
        required = ["base_url", "serie_name", "start_episode", "end_episode"]
        return all(key in criteria for key in required)
    
    def _search_series(self, base_url: str, serie_name: str) -> List[Dict[str, Any]]:
        """Busca las series que coinciden con el nombre"""
        logger.info(f"Buscando serie '{serie_name}' en {base_url}/buscar")
        
        search_url = f"{base_url}/buscar"
        data = {"valor": serie_name, "Buscar": "Buscar"}
        
        try:
            response = requests.post(search_url, data=data, timeout=10, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            series_links = soup.find_all("a", href=re.compile(r"/serie/"))
            
            logger.info(f"Encontrados {len(series_links)} enlaces potenciales de series")
            
            series_found = []
            for link in series_links:
                href = link["href"]
                title = link.text.strip()
                
                match_serie, series_name_extracted = self._matches_series_name(title, serie_name)
                if match_serie:
                    logger.info(f"¡Serie coincidente encontrada: '{title}'!")
                    series_found.append({
                        "title": series_name_extracted,
                        "title_original": title,
                        "url": f"{base_url}{href}",
                        "href": href
                    })
            
            logger.info(f"Total de series coincidentes: {len(series_found)}")
            return series_found
            
        except Exception as e:
            logger.error(f"Error buscando series: {e}")
            return []
    
    def _matches_series_name(self, title: str, search_name: str) -> tuple:
        """Verifica si el título de la serie coincide con la búsqueda"""
        logger.info(f"Comparando título '{title}' con búsqueda '{search_name}'")
        
        series_name_from_title = self._extract_series_name_from_title(title)
        
        title_norm = series_name_from_title.lower().replace(" ", "")
        search_norm = search_name.lower().replace(" ", "")
        
        if title_norm == search_norm or title_norm.startswith(search_norm) or search_norm.startswith(title_norm):
            match = True
        else:
            match = False
        
        logger.info(f"Nombre extraído: '{series_name_from_title}' -> match = {match}")
        return match, series_name_from_title
    
    def _extract_series_name_from_title(self, title: str) -> str:
        """Extrae el nombre de la serie del título completo"""
        separators = [" - ", " – ", " | ", " : ", " temporada ", " season "]
        
        for separator in separators:
            if separator.lower() in title.lower():
                parts = title.split(separator, 1)
                if len(parts) > 1:
                    series_name = parts[0].strip()
                    series_name = re.sub(r'[^\w\sÀ-ÿ]', '', series_name).strip()
                    return series_name
        
        return re.sub(r'[^\w\sÀ-ÿ]', '', title).strip()
    
    def _get_episodes(self, serie_data: Dict, base_url: str, start_episode: str, 
                     end_episode: str, calidad: str = None) -> List[Dict[str, Any]]:
        """Obtiene los episodios de una temporada específica"""
        try:
            logger.info(f"Obteniendo episodios de {serie_data['url']}")
            
            response = requests.get(serie_data["url"], timeout=10, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extraer formato de la serie
            episode_format, format_string_original = self._extract_series_format_category(soup)
            
            # Buscar tabla de episodios
            tabla = soup.find("table")
            if not tabla:
                logger.warning(f"No se encontró la tabla de episodios en {serie_data['url']}")
                return []
            
            tbody = tabla.find("tbody")
            if not tbody:
                logger.warning(f"No se encontró tbody en la tabla")
                return []
            
            filas = tbody.find_all("tr")
            if not filas or len(filas) < 1:
                logger.warning(f"No se encontraron filas de episodios")
                return []
            
            torrents = []
            for fila in filas:
                columnas = fila.find_all("td")
                
                if len(columnas) < 2:
                    logger.warning(f"Fila con formato inesperado, omitiendo")
                    continue
                
                # Extraer código de episodio
                episode_code = self._extract_episode_code(columnas[0].text.strip())
                if not episode_code:
                    continue
                
                episode_code = f"{episode_format}{episode_code}"
                status = episode_code
                
                # Validar formato
                if not self._is_valid_status_format(status):
                    logger.warning(f"Formato de status inválido: '{status}', omitiendo episodio")
                    continue
                
                # Verificar rango
                if not self._is_in_range(episode_code, start_episode, end_episode):
                    logger.debug(f"Episodio fuera de rango: {episode_code}, omitiendo")
                    continue
                
                # Obtener enlace protegido
                enlace = columnas[1].find("a")
                if not enlace:
                    continue
                
                content_id = enlace.get("data-content-id")
                if not content_id:
                    continue
                
                try:
                    protected_url = self._get_protected_download_url(content_id, "series", base_url)
                    protected_url = f"{base_url}{protected_url}"
                    
                    torrent = {
                        "status": status,
                        "format": format_string_original,
                        "title": serie_data["title"],
                        "title_original": serie_data["title_original"],
                        "link": protected_url,
                        "episode_code": episode_code
                    }
                    torrents.append(torrent)
                    
                except Exception as e:
                    logger.error(f"Error obteniendo URL protegida para episodio {episode_code}: {e}")
                    continue
            
            logger.info(f"Se encontraron {len(torrents)} torrents en la temporada '{serie_data['title']}'")
            return torrents
            
        except Exception as e:
            logger.error(f"Error obteniendo episodios de {serie_data['url']}: {e}")
            return []
    
    def _get_protected_download_url(self, content_id: str, tabla: str, base_url: str) -> str:
        """Obtiene la URL de descarga protegida usando PoW"""
        try:
            # 1. Generar challenge
            generate_url = f"{base_url}/api_validate_pow.php"
            generate_payload = {
                "action": "generate",
                "content_id": int(content_id),
                "tabla": tabla
            }
            
            logger.debug(f"Generando challenge para content_id: {content_id}")
            response = requests.post(generate_url, json=generate_payload, timeout=10)
            result = response.json()
            
            if not response.ok or not result.get('success'):
                raise Exception(result.get('error', 'Error generando challenge'))
            
            challenge = result['challenge']
            logger.debug(f"Challenge recibido: {challenge}")
            
            # 2. Computar Proof of Work
            logger.debug("Computando Proof of Work...")
            nonce = self._compute_proof_of_work(challenge, 4)
            logger.debug(f"Nonce encontrado: {nonce}")
            
            # 3. Validar con el servidor
            validate_payload = {
                "action": "validate",
                "challenge": challenge,
                "nonce": nonce
            }
            
            response = requests.post(generate_url, json=validate_payload, timeout=10)
            result = response.json()
            
            if not response.ok or not result.get('success'):
                raise Exception(result.get('error', 'Error en validación'))
            
            logger.debug("Validación exitosa. Descarga permitida.")
            return result['download_url']
            
        except Exception as e:
            logger.error(f"Error en proceso PoW: {e}")
            raise
    
    def _compute_proof_of_work(self, challenge: str, difficulty: int = 4) -> int:
        """Computa Proof of Work"""
        nonce = 0
        target = '0' * difficulty
        
        while True:
            text = challenge + str(nonce)
            hash_hex = hashlib.sha256(text.encode()).hexdigest()
            
            if hash_hex.startswith(target):
                return nonce
            
            nonce += 1
            
            if nonce % 1000 == 0:
                time.sleep(0.001)
    
    def _extract_episode_code(self, title: str) -> str:
        """Extrae el código de episodio del título"""
        patterns = [
            r'S(\d{1,2})E(\d{1,3})',  # S01E01
            r'(\d{1,2})x(\d{1,3})',   # 1x01
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                season = match.group(1).zfill(2)
                episode = match.group(2).zfill(2)
                return f"S{season}E{episode}"
        
        return None
    
    def _extract_series_format_category(self, soup: BeautifulSoup) -> tuple:
        """
        Extrae el formato de la serie y su categoría.
        Formatos válidos: 4K, 1080p, 720p, SD
        Todo lo desconocido se categoriza como SD
        """
        raw_format = self._extract_series_format(soup)
        logger.info(f"Formato raw extraído: {raw_format}")
        
        # Normalizar formato a valores válidos
        format_string = self._normalize_format(raw_format)
        logger.info(f"Formato normalizado: {format_string}")
        
        # Determinar categoría HD o SD
        if format_string in ["4K", "1080p", "720p"]:
            return "HD", format_string
        else:
            return "SD", format_string
    
    def _extract_series_format(self, soup: BeautifulSoup) -> str:
        """
        Extrae el formato de la serie desde el HTML.
        Busca en múltiples ubicaciones del HTML.
        Retorna el formato raw encontrado o None si no encuentra nada.
        """
        # Método 1: Title tag
        title_tag = soup.find("title")
        if title_tag:
            match = re.search(r"\[(\d{3,4}p|4K)\]", title_tag.text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        # Método 2: H2 con clase descargarTitulo
        h2_tag = soup.find("h2", class_="descargarTitulo")
        if h2_tag:
            match = re.search(r"\[(\d{3,4}p|4K)\]", h2_tag.text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        # Método 3: Párrafo con "Formato:"
        formato_p = soup.find("p", string=re.compile(r"Formato:"))
        if formato_p:
            match = re.search(r"Formato:\s*([^\s<]+)", formato_p.text)
            if match:
                formato_full = match.group(1)
                res_match = re.search(r"(\d{3,4}p|4K)", formato_full, re.IGNORECASE)
                if res_match:
                    return res_match.group(1).upper()
        
        # Método 4: Buscar en cualquier parte del texto que contenga resoluciones
        body_text = soup.get_text()
        match = re.search(r'\b(4K|2160p|1080p|720p)\b', body_text, re.IGNORECASE)
        if match:
            found = match.group(1).upper()
            # Normalizar 2160p a 4K
            if found == "2160P":
                return "4K"
            return found
        
        return None
    
    def _normalize_format(self, raw_format: str) -> str:
        """
        Normaliza el formato a valores válidos: 4K, 1080p, 720p, SD
        Cualquier formato desconocido o None se convierte en SD
        """
        if not raw_format:
            return "SD"
        
        raw_format = raw_format.upper().strip()
        
        # Formatos válidos
        valid_formats = {
            "4K": "4K",
            "2160P": "4K",  # 2160p es 4K
            "1080P": "1080p",
            "720P": "720p",
        }
        
        # Intentar match exacto
        if raw_format in valid_formats:
            return valid_formats[raw_format]
        
        # Intentar extraer número de resolución
        match = re.search(r'(\d{3,4})p?', raw_format, re.IGNORECASE)
        if match:
            resolution = int(match.group(1))
            
            # Mapear a formatos válidos
            if resolution >= 2160:
                return "4K"
            elif resolution >= 1080:
                return "1080p"
            elif resolution >= 720:
                return "720p"
        
        # Si contiene "4K" en cualquier parte
        if "4K" in raw_format or "UHD" in raw_format:
            return "4K"
        
        # Por defecto, todo lo demás es SD
        logger.warning(f"Formato desconocido '{raw_format}', usando SD por defecto")
        return "SD"
    
    def _is_in_range(self, episode_code: str, start: str, end: str) -> bool:
        """
        Verifica si un episodio está dentro del rango especificado.
        Ahora soporta rangos que cruzan temporadas.
        """
        try:
            # Remover prefijo HD/SD si existe
            clean_code = re.sub(r'^(HD|SD)', '', episode_code)
            clean_start = re.sub(r'^(HD|SD)', '', start)
            clean_end = re.sub(r'^(HD|SD)', '', end)
            
            # Extraer temporada y episodio del código actual
            current_match = re.search(r'S(\d+)E(\d+)', clean_code, re.IGNORECASE)
            if not current_match:
                return False
                
            current_season = int(current_match.group(1))
            current_episode = int(current_match.group(2))
            
            # Verificar contra start
            start_match = re.search(r'S(\d+)E(\d+)', clean_start, re.IGNORECASE)
            if start_match:
                start_season = int(start_match.group(1))
                start_episode_num = int(start_match.group(2))
                
                # Si es temporada anterior, excluir
                if current_season < start_season:
                    return False
                # Si es la misma temporada, verificar episodio
                elif current_season == start_season and current_episode < start_episode_num:
                    return False
            
            # Verificar contra end
            end_match = re.search(r'S(\d+)E(\d+)', clean_end, re.IGNORECASE)
            if end_match:
                end_season = int(end_match.group(1))
                end_episode_num = int(end_match.group(2))
                
                # Si es temporada posterior, excluir
                if current_season > end_season:
                    return False
                # Si es la misma temporada, verificar episodio
                elif current_season == end_season and current_episode > end_episode_num:
                    return False
            
            return True
        except:
            return False
    
    def _episode_to_number(self, episode_code: str) -> int:
        """Convierte un código de episodio a número para comparación"""
        # Remover prefijo HD/SD si existe
        clean_code = re.sub(r'^(HD|SD)', '', episode_code)
        
        if "S" in clean_code and "E" in clean_code:
            season = int(clean_code.split("S")[1].split("E")[0])
            episode = int(clean_code.split("E")[1])
            return season * 1000 + episode
        return 0
    
    def _is_valid_status_format(self, status: str) -> bool:
        """Verifica que el status tenga el formato correcto: HDS01E02 o SDS99E99"""
        pattern = r'^(HD|SD)S\d{2}E\d{2}$'
        return bool(re.match(pattern, status))
    
    def _get_format_priority(self, format_str: str) -> int:
        """
        Asigna prioridad al formato para ordenamiento.
        Orden de preferencia: 720p > 1080p > 4K > SD
        Solo reconoce formatos válidos.
        """
        if not format_str:
            return 0
        
        format_str = format_str.upper().strip()
        
        # Mapeo de prioridades (mayor número = mayor preferencia)
        # Orden: 720p primero, luego 1080p, luego 4K, finalmente SD
        priorities = {
            "720P": 4,    # Máxima prioridad
            "1080P": 3,   # Segunda prioridad
            "4K": 2,      # Tercera prioridad
            "SD": 1       # Mínima prioridad
        }
        
        return priorities.get(format_str, 0)
