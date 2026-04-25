from fastapi import APIRouter
import urllib.request, json

router = APIRouter()

@router.get("/api/health")
def health():
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as r:
            data = json.loads(r.read())
            modelos = [m["name"] for m in data.get("models", [])]
            return {"status": "ok", "ollama": True, "modelos": modelos}
    except Exception:
        return {"status": "ok", "ollama": False, "modelos": [],
                "aviso": "Ollama no detectado. Inicia Ollama para usar el agente."}
