"""
app/memoria.py
==============
Memoria persistente del proyecto Unity.
- Contexto del proyecto (clave/valor)
- Historial de generaciones/correcciones
- Convenciones de codigo
- Backups para revertir cambios (snapshots de archivos)
- Aprendizaje automatico desde scripts subidos
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.environ.get("COGNIADEV_DB", "cognia_dev.db")


def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with _conn() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS proyecto (
            clave   TEXT PRIMARY KEY,
            valor   TEXT NOT NULL,
            updated TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS historial (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo      TEXT NOT NULL,
            entrada   TEXT NOT NULL,
            salida    TEXT NOT NULL,
            created   TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS convenciones (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo    TEXT NOT NULL,
            contenido TEXT NOT NULL,
            created   TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS backups (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            archivo_path      TEXT NOT NULL,
            contenido_antes   TEXT NOT NULL,
            contenido_despues TEXT NOT NULL,
            descripcion       TEXT NOT NULL,
            created           TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS scripts_aprendidos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT NOT NULL UNIQUE,
            contenido TEXT NOT NULL,
            resumen   TEXT NOT NULL,
            created   TEXT NOT NULL
        );
        """)


# ── Proyecto ────────────────────────────────────────────────────────────────

def set_proyecto(clave: str, valor: str):
    with _conn() as con:
        con.execute(
            "INSERT OR REPLACE INTO proyecto (clave, valor, updated) VALUES (?,?,?)",
            (clave, valor, datetime.now().isoformat())
        )

def get_proyecto(clave: str) -> Optional[str]:
    with _conn() as con:
        row = con.execute("SELECT valor FROM proyecto WHERE clave=?", (clave,)).fetchone()
        return row["valor"] if row else None

def get_todo_proyecto() -> dict:
    with _conn() as con:
        rows = con.execute("SELECT clave, valor FROM proyecto").fetchall()
        return {r["clave"]: r["valor"] for r in rows}

def delete_proyecto(clave: str):
    with _conn() as con:
        con.execute("DELETE FROM proyecto WHERE clave=?", (clave,))


# ── Historial ───────────────────────────────────────────────────────────────

def guardar_historial(tipo: str, entrada: str, salida: str):
    with _conn() as con:
        con.execute(
            "INSERT INTO historial (tipo, entrada, salida, created) VALUES (?,?,?,?)",
            (tipo, entrada, salida, datetime.now().isoformat())
        )

def get_historial(limite: int = 20) -> list:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM historial ORDER BY id DESC LIMIT ?", (limite,)
        ).fetchall()
        return [dict(r) for r in rows]

def delete_historial_item(id: int):
    with _conn() as con:
        con.execute("DELETE FROM historial WHERE id=?", (id,))


# ── Convenciones ─────────────────────────────────────────────────────────────

def agregar_convencion(titulo: str, contenido: str):
    with _conn() as con:
        con.execute(
            "INSERT INTO convenciones (titulo, contenido, created) VALUES (?,?,?)",
            (titulo, contenido, datetime.now().isoformat())
        )

def get_convenciones() -> list:
    with _conn() as con:
        rows = con.execute("SELECT * FROM convenciones ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

def delete_convencion(id: int):
    with _conn() as con:
        con.execute("DELETE FROM convenciones WHERE id=?", (id,))


# ── Backups / Reversion ──────────────────────────────────────────────────────

def guardar_backup(archivo_path: str, contenido_antes: str, contenido_despues: str, descripcion: str) -> int:
    with _conn() as con:
        cur = con.execute(
            "INSERT INTO backups (archivo_path, contenido_antes, contenido_despues, descripcion, created) VALUES (?,?,?,?,?)",
            (archivo_path, contenido_antes, contenido_despues, descripcion, datetime.now().isoformat())
        )
        return cur.lastrowid

def get_backups(archivo_path: Optional[str] = None, limite: int = 50) -> list:
    with _conn() as con:
        if archivo_path:
            rows = con.execute(
                "SELECT id, archivo_path, descripcion, created FROM backups WHERE archivo_path=? ORDER BY id DESC LIMIT ?",
                (archivo_path, limite)
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT id, archivo_path, descripcion, created FROM backups ORDER BY id DESC LIMIT ?",
                (limite,)
            ).fetchall()
        return [dict(r) for r in rows]

def get_backup_by_id(backup_id: int) -> Optional[dict]:
    with _conn() as con:
        row = con.execute("SELECT * FROM backups WHERE id=?", (backup_id,)).fetchone()
        return dict(row) if row else None

def delete_backup(backup_id: int):
    with _conn() as con:
        con.execute("DELETE FROM backups WHERE id=?", (backup_id,))


# ── Scripts Aprendidos ───────────────────────────────────────────────────────

def guardar_script_aprendido(nombre: str, contenido: str, resumen: str):
    with _conn() as con:
        con.execute(
            "INSERT INTO scripts_aprendidos (nombre, contenido, resumen, created) VALUES (?,?,?,?) "
            "ON CONFLICT(nombre) DO UPDATE SET contenido=excluded.contenido, resumen=excluded.resumen, created=excluded.created",
            (nombre, contenido, resumen, datetime.now().isoformat())
        )

def get_scripts_aprendidos() -> list:
    with _conn() as con:
        rows = con.execute("SELECT * FROM scripts_aprendidos ORDER BY created DESC").fetchall()
        return [dict(r) for r in rows]

def delete_script_aprendido(id: int):
    with _conn() as con:
        con.execute("DELETE FROM scripts_aprendidos WHERE id=?", (id,))


# ── Contexto enriquecido para Ollama ─────────────────────────────────────────

def build_contexto_completo() -> Optional[str]:
    partes = []

    proyecto = get_todo_proyecto()
    if proyecto:
        partes.append("=== PROYECTO ===")
        for k, v in proyecto.items():
            partes.append(f"{k}: {v}")

    convenciones = get_convenciones()
    if convenciones:
        partes.append("\n=== CONVENCIONES DE CODIGO ===")
        for c in convenciones:
            partes.append(f"- {c['titulo']}: {c['contenido']}")

    scripts = get_scripts_aprendidos()
    if scripts:
        partes.append("\n=== SCRIPTS DEL PROYECTO (referencia) ===")
        for s in scripts[:8]:
            partes.append(f"\n--- {s['nombre']} ---")
            partes.append(s['resumen'])

    historial = get_historial(limite=5)
    if historial:
        partes.append("\n=== ULTIMAS INTERACCIONES ===")
        for h in reversed(historial):
            tipo = "Generacion" if h["tipo"] == "generar" else "Correccion"
            partes.append(f"[{tipo}] {h['entrada'][:120]}...")

    return "\n".join(partes) if partes else None


init_db()
