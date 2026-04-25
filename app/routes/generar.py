from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.ollama_client import generar_codigo
from app.memoria import guardar_historial, build_contexto_completo

router = APIRouter()

class GenerarRequest(BaseModel):
    instruccion: str
    contexto: Optional[str] = None  # contexto manual (override)
    usar_memoria: bool = True        # inyectar memoria del proyecto automaticamente

class GenerarResponse(BaseModel):
    codigo: str
    contexto_usado: str = ""
    error: str = ""

@router.post("/api/generar", response_model=GenerarResponse)
def generar(req: GenerarRequest):
    if not req.instruccion.strip():
        return GenerarResponse(codigo="", error="Instruccion vacia.")

    # Contexto: manual > memoria automatica > ninguno
    contexto = req.contexto
    if not contexto and req.usar_memoria:
        contexto = build_contexto_completo()

    resultado = generar_codigo(req.instruccion.strip(), contexto)
    if not resultado["ok"]:
        return GenerarResponse(codigo="", error=resultado["error"])

    guardar_historial("generar", req.instruccion.strip(), resultado["response"][:500])
    return GenerarResponse(
        codigo=resultado["response"],
        contexto_usado=contexto or "",
    )
