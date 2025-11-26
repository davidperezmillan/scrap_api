from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Web Scraping API",
    description="API modular para scraping de múltiples sitios web",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(router)

# Event handlers
@app.on_event("startup")
async def startup_event():
    """Evento al iniciar la aplicación"""
    logger.info("Starting Web Scraping API...")
    logger.info("API documentation available at /docs")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento al cerrar la aplicación"""
    logger.info("Shutting down Web Scraping API...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
