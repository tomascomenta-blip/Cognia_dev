"""
app/routes/memoria.py
=====================
Endpoints para gestionar la memoria del proyecto.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.memoria import (
    set_proyecto, get_todo_proyecto, delete_proyecto,
    agregar_convencion, get_convenciones, delete_convencion,
    get_historial, delete_historial_item,
    build_contexto_completo,
)

router = APIRouter(prefix="/api/memoria")


# ── Proyecto ────────────────────────────────────────────────────────────────

class ProyectoItem(BaseModel):
    clave: str
    valor: str

@router.get("/proyecto")
def proyecto_get():
    return {"datos": get_todo_proyecto()}

@router.post("/proyecto")
def proyecto_set(item: ProyectoItem):
    set_proyecto(item.clave, item.valor)
    return {"ok": True}

@router.delete("/proyecto/{clave}")
def proyecto_delete(clave: str):
    delete_proyecto(clave)
    return {"ok": True}


# ── Convenciones ─────────────────────────────────────────────────────────────

class ConvencionItem(BaseModel):
    titulo: str
    contenido: str

@router.get("/convenciones")
def convenciones_get():
    return {"convenciones": get_convenciones()}

@router.post("/convenciones")
def convenciones_post(item: ConvencionItem):
    agregar_convencion(item.titulo, item.contenido)
    return {"ok": True}

@router.delete("/convenciones/{id}")
def convenciones_delete(id: int):
    delete_convencion(id)
    return {"ok": True}


# ── Historial ────────────────────────────────────────────────────────────────

@router.get("/historial")
def historial_get():
    return {"historial": get_historial(30)}

@router.delete("/historial/{id}")
def historial_delete(id: int):
    delete_historial_item(id)
    return {"ok": True}


# ── Contexto completo ─────────────────────────────────────────────────────────

@router.get("/contexto")
def contexto_get():
    ctx = build_contexto_completo()
    return {"contexto": ctx or ""}
