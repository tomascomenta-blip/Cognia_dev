"""
app/ollama_client.py
====================
Cliente para Ollama local con system prompts especializados en Unity/C#.
Incluye soporte de "thinking" visible: el modelo razona en voz alta antes de responder.
"""

import urllib.request
import urllib.error
import json
from typing import Optional

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL      = "qwen2.5-coder:7b"
TIMEOUT    = 1200  # 20 minutos - ajusta aqui si necesitas mas tiempo

# Instruccion de thinking que se antepone a todos los system prompts
_THINKING_PREFIX = """Antes de escribir cualquier codigo, razona en voz alta entre las etiquetas <thinking> y </thinking>.
En ese bloque explica brevemente: que vas a hacer, que clases/metodos de Unity usaras, y si hay algun riesgo o decision importante.
Luego escribe el codigo fuera de esas etiquetas, sin repetir el razonamiento.

Ejemplo de formato correcto:
<thinking>
El usuario quiere un sistema de salud. Usare una variable float, la expondere con [SerializeField].
Necesito un metodo publico TakeDamage(float amount) y un evento OnDeath para notificar al resto del juego.
</thinking>
using UnityEngine;
public class Health : MonoBehaviour { ... }

"""

SYSTEM_UNITY = _THINKING_PREFIX + """Eres un experto en desarrollo de videojuegos con Unity y C#.
Reglas estrictas que SIEMPRE debes seguir:
- Responde SOLO con codigo C# limpio y funcional, listo para Unity.
- Usa el namespace UnityEngine cuando corresponda.
- Sigue las convenciones de Unity: MonoBehaviour, Start(), Update(), etc.
- No inventes APIs que no existen en Unity.
- El codigo debe compilar sin errores.
- Usa [SerializeField] en vez de public para variables del inspector cuando sea posible.
- Agrega comentarios breves en espanol explicando las partes clave.
- Si hay contexto de proyecto, respeta sus convenciones y arquitectura.
"""

SYSTEM_CORRECCION = _THINKING_PREFIX + """Eres un experto en debugging de C# para Unity.
Reglas estrictas:
- Analiza el codigo recibido e identifica TODOS los problemas.
- Devuelve el codigo corregido completo (no solo el fragmento cambiado).
- Despues del codigo, lista los cambios realizados en formato:
  CAMBIOS:
  1. [descripcion breve del cambio]
  2. [descripcion breve del cambio]
- Si el codigo no tiene errores, dilo claramente y sugiere mejoras opcionales.
- Si hay contexto de proyecto, respeta sus convenciones.
"""


def _extraer_thinking(raw: str) -> tuple[str, str]:
    """
    Separa el bloque <thinking>...</thinking> del codigo real.
    Retorna (thinking, codigo).
    """
    thinking = ""
    codigo   = raw

    if "<thinking>" in raw and "</thinking>" in raw:
        t_start  = raw.index("<thinking>") + len("<thinking>")
        t_end    = raw.index("</thinking>")
        thinking = raw[t_start:t_end].strip()
        codigo   = raw[t_end + len("</thinking>"):].strip()

    return thinking, codigo


def _llamar_ollama(prompt: str, system: str, temperatura: float = 0.2) -> dict:
    payload = json.dumps({
        "model":   MODEL,
        "prompt":  prompt,
        "system":  system,
        "stream":  False,
        "options": {
            "temperature":  temperatura,
            "num_predict":  2048,
        },
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data    = json.loads(resp.read().decode())
            raw     = data.get("response", "").strip()
            thinking, codigo = _extraer_thinking(raw)
            return {
                "ok":       True,
                "response": codigo,
                "thinking": thinking,
            }
    except urllib.error.URLError as e:
        return {"ok": False, "error": f"Ollama no responde: {e}. Asegurate de que Ollama este corriendo."}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def generar_codigo(instruccion: str, contexto: Optional[str] = None) -> dict:
    prompt = instruccion
    if contexto:
        prompt = f"Contexto del proyecto:\n{contexto}\n\nInstruccion:\n{instruccion}"
    return _llamar_ollama(prompt, SYSTEM_UNITY, temperatura=0.2)


def corregir_codigo(codigo: str, error: Optional[str] = None, contexto: Optional[str] = None) -> dict:
    prompt = f"Codigo a corregir:\n```csharp\n{codigo}\n```"
    if error:
        prompt += f"\n\nError reportado:\n{error}"
    if contexto:
        prompt = f"Contexto del proyecto:\n{contexto}\n\n" + prompt
    return _llamar_ollama(prompt, SYSTEM_CORRECCION, temperatura=0.1)
