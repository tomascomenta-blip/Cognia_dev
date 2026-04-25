from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.ollama_client import generar_codigo

router = APIRouter()

class GenerarRequest(BaseModel):
    instruccion: str
    contexto: Optional[str] = None

class GenerarResponse(BaseModel):
    codigo: str
    error: str = ""

@router.post("/api/generar", response_model=GenerarResponse)
def generar(req: GenerarRequest):
    if not req.instruccion.strip():
        return GenerarResponse(codigo="", error="Instruccion vacia.")
    resultado = generar_codigo(req.instruccion.strip(), req.contexto)
    if not resultado["ok"]:
        return GenerarResponse(codigo="", error=resultado["error"])
    return GenerarResponse(codigo=resultado["response"])
