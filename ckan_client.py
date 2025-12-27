from __future__ import annotations
import requests

CKAN_BASE = "https://datos.gob.cl"
ACTION_BASE = f"{CKAN_BASE}/api/3/action"

class CKANError(RuntimeError):
    pass

def ckan_get(action: str, params: dict | None = None, timeout: int = 30) -> dict:
    """Llama a la API CKAN Action por GET y retorna result (dict)."""
    url = f"{ACTION_BASE}/{action}"
    r = requests.get(url, params=params or {}, timeout=timeout)
    r.raise_for_status()
    payload = r.json()
    if not payload.get("success", False):
        raise CKANError(payload.get("error", "Respuesta CKAN no exitosa"))
    return payload["result"]

def package_show(package_id: str) -> dict:
    return ckan_get("package_show", {"id": package_id})

def resource_show(resource_id: str) -> dict:
    return ckan_get("resource_show", {"id": resource_id})

def download_resource(url: str, timeout: int = 60) -> bytes:
    """Descarga un archivo vía GET y retorna bytes."""
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.content
