from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.ollama_client import corregir_codigo

router = APIRouter()

class CorregirRequest(BaseModel):
    codigo: str
    error: Optional[str] = None

class CorregirResponse(BaseModel):
    codigo_corregido: str
    cambios: str = ""
    error: str = ""

@router.post("/api/corregir", response_model=CorregirResponse)
def corregir(req: CorregirRequest):
    if not req.codigo.strip():
        return CorregirResponse(codigo_corregido="", error="Codigo vacio.")
    resultado = corregir_codigo(req.codigo.strip(), req.error)
    if not resultado["ok"]:
        return CorregirResponse(codigo_corregido="", error=resultado["error"])
    respuesta = resultado["response"]
    # Separar codigo de cambios si el modelo los incluye
    cambios = ""
    if "CAMBIOS:" in respuesta:
        partes = respuesta.split("CAMBIOS:", 1)
        respuesta = partes[0].strip()
        cambios = "CAMBIOS:\n" + partes[1].strip()
    return CorregirResponse(codigo_corregido=respuesta, cambios=cambios)
