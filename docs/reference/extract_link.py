import requests
import hashlib
import time
import json

import logging
logger = logging.getLogger(__name__)


def compute_proof_of_work(challenge, difficulty=4):
    """
    Función para computar Proof of Work.
    Encuentra un nonce tal que SHA-256(challenge + nonce) comience con 'difficulty' ceros.
    """
    nonce = 0
    target = '0' * difficulty

    while True:
        text = challenge + str(nonce)
        hash_obj = hashlib.sha256(text.encode())
        hash_hex = hash_obj.hexdigest()

        if hash_hex.startswith(target):
            return nonce

        nonce += 1

        # Yield para no bloquear (en Python, simular con sleep mínimo)
        if nonce % 1000 == 0:
            time.sleep(0.001)  # Pequeño delay para simular yield


def get_protected_download_url(content_id, tabla, base_url):
    """
    Obtiene la URL de descarga protegida haciendo las llamadas PoW.
    """
    try:
        # 1. Generar challenge (llamada al servidor)
        generate_url = f"{base_url}/api_validate_pow.php"
        generate_payload = {
            "action": "generate",
            "content_id": int(content_id),
            "tabla": tabla
        }
        logger.info(f"Enviando POST a {generate_url} con payload: {json.dumps(generate_payload)}")
        generate_response = requests.post(generate_url, json=generate_payload, timeout=10)
        generate_result = generate_response.json()

        if not generate_response.ok or not generate_result.get('success'):
            raise Exception(generate_result.get('error', 'Error generando challenge'))

        challenge = generate_result['challenge']
        logger.info(f"Challenge recibido: {challenge}")

        # 2. Ejecutar Proof of Work
        logger.info("Computando Proof of Work...")
        start_time = time.time()
        nonce = compute_proof_of_work(challenge, 4)
        end_time = time.time()
        logger.info(f"Nonce encontrado: {nonce} en {end_time - start_time:.2f} segundos")

        # 3. Enviar al servidor para validación
        validate_payload = {
            "action": "validate",
            "challenge": challenge,
            "nonce": nonce
        }
        logger.info(f"Enviando POST a {generate_url} con payload: {json.dumps(validate_payload)}")
        response = requests.post(generate_url, json=validate_payload, timeout=10)
        result = response.json()

        if not response.ok or not result.get('success'):
            raise Exception(result.get('error', 'Error en validación'))

        logger.info("Validación exitosa. Descarga permitida.")
        download_url = result['download_url']
        return download_url

    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión: {e}")
        raise
    except Exception as e:
        logger.error(f"Error en el proceso PoW: {e}")
        raise