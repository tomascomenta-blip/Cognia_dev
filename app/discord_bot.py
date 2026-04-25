"""
app/discord_bot.py
==================
Bot de Discord integrado con Cognia Dev.
- Envia resultados de generar/corregir al canal configurado
- Escucha comandos !generar y !corregir desde Discord
- Permite calificar resultados con reacciones 👍 👎
- Muestra historial con !historial
"""

import discord
import asyncio
import os
import threading
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN  = os.getenv("DISCORD_BOT_TOKEN", "")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

# Intents necesarios
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

client = discord.Client(intents=intents)

# Cola para enviar mensajes desde FastAPI al bot
_message_queue: asyncio.Queue = None
# Loop del bot (para poder encolar desde otros threads)
_bot_loop: asyncio.AbstractEventLoop = None
# Historial en memoria: lista de dicts {tipo, thinking, resultado, msg_id, calificacion}
_historial: list = []


# ── Eventos del bot ────────────────────────────────────────────────────────────

@client.event
async def on_ready():
    print(f"[Cognia Discord] Bot conectado como {client.user}")
    canal = client.get_channel(CHANNEL_ID)
    if canal:
        await canal.send("✅ **Cognia Dev** conectado y listo. Usá `!ayuda` para ver los comandos.")


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    if message.channel.id != CHANNEL_ID:
        return

    texto = message.content.strip()

    if texto == "!ayuda":
        await message.channel.send(
            "**Comandos disponibles:**\n"
            "`!generar <instruccion>` — genera código C# para Unity\n"
            "`!corregir` — en el siguiente mensaje pegá el código a corregir\n"
            "`!historial` — muestra los últimos 5 resultados\n"
            "👍 / 👎 — reaccioná a un resultado para calificarlo"
        )

    elif texto.startswith("!generar "):
        instruccion = texto[len("!generar "):].strip()
        if not instruccion:
            await message.channel.send("⚠️ Escribí la instrucción después de `!generar`.")
            return
        await message.channel.send(f"⏳ Generando código para: *{instruccion}*...")
        # Importar aquí para evitar circular imports
        from app.ollama_client import generar_codigo
        from app.memoria import build_contexto_completo
        contexto = build_contexto_completo()
        resultado = await asyncio.get_event_loop().run_in_executor(
            None, lambda: generar_codigo(instruccion, contexto)
        )
        await _enviar_resultado(message.channel, "generar", instruccion, resultado)

    elif texto == "!corregir":
        await message.channel.send("📋 Pegá el código C# en el siguiente mensaje.")
        # Esperar el siguiente mensaje del mismo usuario
        def check(m):
            return m.author == message.author and m.channel.id == CHANNEL_ID
        try:
            resp = await client.wait_for("message", check=check, timeout=120)
            codigo = resp.content.strip()
            await message.channel.send("⏳ Corrigiendo código...")
            from app.ollama_client import corregir_codigo
            from app.memoria import build_contexto_completo
            contexto = build_contexto_completo()
            resultado = await asyncio.get_event_loop().run_in_executor(
                None, lambda: corregir_codigo(codigo, None, contexto)
            )
            await _enviar_resultado(message.channel, "corregir", codigo[:100] + "...", resultado)
        except asyncio.TimeoutError:
            await message.channel.send("⏰ Tiempo de espera agotado.")

    elif texto == "!historial":
        if not _historial:
            await message.channel.send("📭 No hay resultados en el historial todavía.")
            return
        ultimos = _historial[-5:]
        for i, item in enumerate(reversed(ultimos), 1):
            cal = {"aprobado": "👍", "rechazado": "👎", None: "⏳ sin calificar"}.get(item.get("calificacion"))
            preview = item["resultado"][:200].replace("```", "")
            await message.channel.send(
                f"**#{i} — {item['tipo'].upper()}** {cal}\n"
                f"*{item['instruccion'][:80]}*\n"
                f"```csharp\n{preview}\n...```"
            )


@client.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user == client.user:
        return
    # Buscar en historial el mensaje calificado
    for item in _historial:
        if item.get("msg_id") == reaction.message.id:
            if str(reaction.emoji) == "👍":
                item["calificacion"] = "aprobado"
                await reaction.message.channel.send(f"✅ Resultado marcado como **aprobado** por {user.display_name}.")
            elif str(reaction.emoji) == "👎":
                item["calificacion"] = "rechazado"
                await reaction.message.channel.send(f"❌ Resultado marcado como **rechazado** por {user.display_name}. Podés usar `!generar` con más detalle.")
            break


# ── Helpers internos ───────────────────────────────────────────────────────────

async def _enviar_resultado(canal, tipo: str, instruccion: str, resultado: dict):
    """Formatea y envía un resultado al canal, con thinking si hay."""
    if not resultado.get("ok", True) and resultado.get("error"):
        await canal.send(f"❌ **Error:** {resultado['error']}")
        return

    codigo   = resultado.get("response", resultado.get("codigo_corregido", ""))
    thinking = resultado.get("thinking", "")

    # Thinking (si existe)
    if thinking:
        # Discord tiene limite de 2000 chars por mensaje
        thinking_msg = f"🧠 **Razonamiento:**\n```\n{thinking[:1500]}\n```"
        await canal.send(thinking_msg)

    # Código resultado
    codigo_preview = codigo[:1400] if len(codigo) > 1400 else codigo
    truncado = "*(truncado — copiá desde Unity para el completo)*" if len(codigo) > 1400 else ""
    sent = await canal.send(
        f"{'✨ Generado' if tipo == 'generar' else '🔧 Corregido'} — *{instruccion[:60]}*\n"
        f"```csharp\n{codigo_preview}\n```{truncado}\n"
        f"Calificá con 👍 o 👎"
    )

    # Agregar reacciones sugeridas
    await sent.add_reaction("👍")
    await sent.add_reaction("👎")

    # Guardar en historial
    _historial.append({
        "tipo":          tipo,
        "instruccion":   instruccion,
        "resultado":     codigo,
        "thinking":      thinking,
        "msg_id":        sent.id,
        "calificacion":  None,
    })
    # Mantener solo los ultimos 20
    if len(_historial) > 20:
        _historial.pop(0)


# ── API pública (llamada desde routes) ────────────────────────────────────────

def notify(tipo: str, instruccion: str, resultado: dict):
    """
    Llamar desde cualquier route para notificar a Discord.
    Thread-safe: encola la corrutina en el loop del bot.
    """
    if not _bot_loop or not client.is_ready():
        return
    canal = client.get_channel(CHANNEL_ID)
    if not canal:
        return
    asyncio.run_coroutine_threadsafe(
        _enviar_resultado(canal, tipo, instruccion, resultado),
        _bot_loop
    )


# ── Arranque ───────────────────────────────────────────────────────────────────

def _run_bot():
    global _bot_loop, _message_queue
    _bot_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_bot_loop)
    _message_queue = asyncio.Queue()
    _bot_loop.run_until_complete(client.start(BOT_TOKEN))


def start_bot_thread():
    """Iniciar el bot en un thread daemon — llamar desde main.py al arrancar FastAPI."""
    if not BOT_TOKEN or not CHANNEL_ID:
        print("[Cognia Discord] ⚠️  BOT_TOKEN o CHANNEL_ID no configurados. Bot desactivado.")
        return
    t = threading.Thread(target=_run_bot, daemon=True)
    t.start()
    print("[Cognia Discord] Bot iniciando en background...")
