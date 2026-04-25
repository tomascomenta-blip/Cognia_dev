"""
app/routes/memoria.py
=====================
Endpoints para gestionar la memoria del proyecto:
- /api/memoria/proyecto       -> contexto clave/valor
- /api/memoria/convenciones   -> reglas de codigo
- /api/memoria/historial      -> historial de generaciones
- /api/memoria/backups        -> reversion de archivos
- /api/memoria/aprender       -> subir script para que la IA aprenda
- /api/memoria/scripts        -> listar/borrar scripts aprendidos
- /api/memoria/contexto       -> ver contexto completo actual
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.memoria import (
    set_proyecto, get_todo_proyecto, delete_proyecto,
    agregar_convencion, get_convenciones, delete_convencion,
    get_historial, delete_historial_item,
    guardar_backup, get_backups, get_backup_by_id, delete_backup,
    guardar_script_aprendido, get_scripts_aprendidos, delete_script_aprendido,
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


# ── Backups / Reversion ──────────────────────────────────────────────────────

class BackupItem(BaseModel):
    archivo_path: str
    contenido_antes: str
    contenido_despues: str
    descripcion: str

class RevertirItem(BaseModel):
    backup_id: int
    aplicar_en_disco: Optional[bool] = False  # si True, escribe el archivo en disco

@router.get("/backups")
def backups_get(archivo_path: Optional[str] = None):
    return {"backups": get_backups(archivo_path)}

@router.get("/backups/{backup_id}")
def backup_detail(backup_id: int):
    b = get_backup_by_id(backup_id)
    if not b:
        raise HTTPException(status_code=404, detail="Backup no encontrado")
    return b

@router.post("/backups")
def backup_crear(item: BackupItem):
    bid = guardar_backup(item.archivo_path, item.contenido_antes, item.contenido_despues, item.descripcion)
    return {"ok": True, "backup_id": bid}

@router.post("/revertir")
def revertir(item: RevertirItem):
    """
    Revierte un archivo a su estado anterior.
    Retorna el contenido_antes para que el plugin lo aplique.
    Si aplicar_en_disco=True y el path existe, lo escribe directamente.
    """
    b = get_backup_by_id(item.backup_id)
    if not b:
        raise HTTPException(status_code=404, detail="Backup no encontrado")

    resultado = {
        "ok": True,
        "archivo_path": b["archivo_path"],
        "contenido_revertido": b["contenido_antes"],
        "escrito_en_disco": False
    }

    if item.aplicar_en_disco:
        import os
        path = b["archivo_path"]
        if os.path.exists(path):
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(b["contenido_antes"])
                resultado["escrito_en_disco"] = True
            except Exception as e:
                resultado["error_disco"] = str(e)
        else:
            resultado["error_disco"] = f"Archivo no encontrado en disco: {path}"

    return resultado

@router.delete("/backups/{backup_id}")
def backup_delete(backup_id: int):
    delete_backup(backup_id)
    return {"ok": True}


# ── Aprendizaje desde scripts ─────────────────────────────────────────────────

class AprenderItem(BaseModel):
    nombre: str          # nombre del script ej: "Plant.cs"
    contenido: str       # contenido completo del archivo
    resumen: Optional[str] = ""  # resumen manual (si esta vacio, se genera automatico)

@router.post("/aprender")
def aprender(item: AprenderItem):
    """
    Recibe un script del proyecto y lo guarda como referencia.
    La IA usara este script como contexto en futuras generaciones/correcciones.
    Si no se pasa resumen, se genera uno automatico con los primeros 800 chars.
    """
    resumen = item.resumen
    if not resumen:
        # Resumen automatico: primeras lineas significativas
        lineas = [l for l in item.contenido.split("\n") if l.strip() and not l.strip().startswith("//")]
        resumen = "\n".join(lineas[:30])

    guardar_script_aprendido(item.nombre, item.contenido, resumen)
    return {"ok": True, "nombre": item.nombre}

@router.get("/scripts")
def scripts_get():
    scripts = get_scripts_aprendidos()
    # No retornar el contenido completo en el listado (puede ser muy grande)
    return {"scripts": [{"id": s["id"], "nombre": s["nombre"], "resumen": s["resumen"][:200], "created": s["created"]} for s in scripts]}

@router.get("/scripts/{script_id}")
def script_detail(script_id: int):
    scripts = get_scripts_aprendidos()
    for s in scripts:
        if s["id"] == script_id:
            return s
    raise HTTPException(status_code=404, detail="Script no encontrado")

@router.delete("/scripts/{script_id}")
def script_delete(script_id: int):
    delete_script_aprendido(script_id)
    return {"ok": True}


# ── Contexto completo ─────────────────────────────────────────────────────────

@router.get("/contexto")
def contexto_get():
    ctx = build_contexto_completo()
    return {"contexto": ctx or ""}
