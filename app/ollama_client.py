"""
app/ollama_client.py
====================
Cliente para Ollama local. Maneja el system prompt especializado en Unity/C#.
"""

import urllib.request
import urllib.error
import json
from typing import Optional

OLLAMA_URL  = "http://localhost:11434/api/generate"
MODEL       = "qwen2.5-coder:7b"
TIMEOUT     = 120

SYSTEM_UNITY = """Eres un experto en desarrollo de videojuegos con Unity y C#.
Reglas estrictas que SIEMPRE debes seguir:
- Responde SOLO con codigo C# limpio y funcional, listo para Unity.
- Usa el namespace UnityEngine cuando corresponda.
- Sigue las convenciones de Unity: MonoBehaviour, Start(), Update(), etc.
- Si el usuario pide explicacion, da primero el codigo y luego una explicacion breve.
- No inventes APIs que no existen en Unity.
- El codigo debe compilar sin errores.
- Usa [SerializeField] en vez de public para variables del inspector cuando sea posible.
- Agrega comentarios breves en espanol explicando las partes clave.
- Si corriges codigo existente, explica brevemente QUE cambiaste y POR QUE.
"""

SYSTEM_CORRECCION = """Eres un experto en debugging de C# para Unity.
Reglas estrictas:
- Analiza el codigo recibido e identifica TODOS los problemas.
- Devuelve el codigo corregido completo (no solo el fragmento cambiado).
- Despues del codigo, lista los cambios realizados en formato:
  CAMBIOS:
  1. [descripcion breve del cambio]
  2. [descripcion breve del cambio]
- Si el codigo no tiene errores, dilo claramente y sugiere mejoras opcionales.
"""


def _llamar_ollama(prompt: str, system: str, temperatura: float = 0.2) -> dict:
    payload = json.dumps({
        "model":   MODEL,
        "prompt":  prompt,
        "system":  system,
        "stream":  False,
        "options": {
            "temperature": temperatura,
            "num_predict": 2048,
        }
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
            return {"ok": True, "response": data.get("response", "").strip()}
    except urllib.error.URLError as e:
        return {"ok": False, "error": f"Ollama no responde: {e}. Asegurate de que Ollama este corriendo."}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def generar_codigo(instruccion: str, contexto: Optional[str] = None) -> dict:
    prompt = instruccion
    if contexto:
        prompt = f"Contexto del proyecto:\n{contexto}\n\nInstruccion:\n{instruccion}"
    return _llamar_ollama(prompt, SYSTEM_UNITY, temperatura=0.2)


def corregir_codigo(codigo: str, descripcion_error: Optional[str] = None) -> dict:
    prompt = f"Codigo a corregir:\n```csharp\n{codigo}\n```"
    if descripcion_error:
        prompt += f"\n\nError reportado:\n{descripcion_error}"
    return _llamar_ollama(prompt, SYSTEM_CORRECCION, temperatura=0.1)
