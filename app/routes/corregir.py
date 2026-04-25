from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.ollama_client import corregir_codigo
from app.memoria import guardar_historial, build_contexto_completo

router = APIRouter()

class CorregirRequest(BaseModel):
    codigo: str
    error: Optional[str] = None
    usar_memoria: bool = True

class CorregirResponse(BaseModel):
    codigo_corregido: str
    cambios: str = ""
    error: str = ""

@router.post("/api/corregir", response_model=CorregirResponse)
def corregir(req: CorregirRequest):
    if not req.codigo.strip():
        return CorregirResponse(codigo_corregido="", error="Codigo vacio.")

    contexto = None
    if req.usar_memoria:
        contexto = build_contexto_completo()

    resultado = corregir_codigo(req.codigo.strip(), req.error, contexto)
    if not resultado["ok"]:
        return CorregirResponse(codigo_corregido="", error=resultado["error"])

    respuesta = resultado["response"]
    cambios = ""
    if "CAMBIOS:" in respuesta:
        partes = respuesta.split("CAMBIOS:", 1)
        respuesta = partes[0].strip()
        cambios = "CAMBIOS:\n" + partes[1].strip()

    guardar_historial("corregir", req.codigo.strip()[:300], respuesta[:500])
    return CorregirResponse(codigo_corregido=respuesta, cambios=cambios)
