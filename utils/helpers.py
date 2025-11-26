# Utils module
# Funciones de utilidad comunes

def clean_text(text: str) -> str:
    """
    Limpia un texto eliminando espacios extras y caracteres especiales.
    
    Args:
        text: Texto a limpiar
        
    Returns:
        Texto limpio
    """
    if not text:
        return ""
    return " ".join(text.split())


def normalize_url(url: str, base_url: str = "") -> str:
    """
    Normaliza una URL, convirtiéndola en absoluta si es relativa.
    
    Args:
        url: URL a normalizar
        base_url: URL base para URLs relativas
        
    Returns:
        URL normalizada
    """
    if not url:
        return ""
    
    if url.startswith("http://") or url.startswith("https://"):
        return url
    
    if base_url:
        return base_url.rstrip("/") + "/" + url.lstrip("/")
    
    return url
