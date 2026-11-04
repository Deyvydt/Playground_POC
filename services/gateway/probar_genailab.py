"""Valida las keys GENAILAB_API_KEY_* del .env: qué modelos ve cada una y cuáles responden de verdad.

Uso (desde la red de TCS o VPN):  .venv\\Scripts\\python probar_genailab.py
No imprime las keys, solo su número.
"""
import json
import os
import urllib.error
import urllib.request

from dotenv import load_dotenv

import certs

certs.apply_to_env()  # CA de Windows: la red de TCS inspecciona TLS
load_dotenv()
BASE = os.getenv("GENAILAB_API_BASE", "https://genailab.tcs.in/v1").rstrip("/")
KEYS = {n: os.environ[f"GENAILAB_API_KEY_{n}"] for n in range(1, 21) if os.getenv(f"GENAILAB_API_KEY_{n}")}
# Orden de preferencia (mejor primero); se prueban solo los que la key realmente lista.
PREFERENCIA = ["sonnet", "gpt-5", "gpt-4.1", "gpt-4o", "gemini", "deepseek", "llama"]


def pedir(key, path, body=None):
    req = urllib.request.Request(
        f"{BASE}/{path}",
        data=json.dumps(body).encode() if body else None,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:150].decode(errors="replace")
    except OSError as e:
        return 0, str(e)[:150]


def rango(modelo):
    m = modelo.lower()
    return next((i for i, p in enumerate(PREFERENCIA) if p in m), len(PREFERENCIA))


funcionan = {}
for n, key in KEYS.items():
    code, data = pedir(key, "models")
    if code != 200:
        print(f"Key {n}: sin acceso ({code}) {data}")
        continue
    modelos = sorted((m["id"] for m in data["data"]), key=rango)
    print(f"Key {n}: {len(modelos)} modelos -> {', '.join(modelos)}")
    for modelo in modelos[:3]:  # prueba real solo de los 3 mejores para no gastar
        code, resp = pedir(key, "chat/completions",
                           {"model": modelo, "messages": [{"role": "user", "content": "Responde solo: ok"}], "max_tokens": 5})
        ok = code == 200
        print(f"   {'OK ' if ok else 'ERR'} {modelo}" + ("" if ok else f" ({code})"))
        if ok:
            funcionan.setdefault(modelo, []).append(n)

if funcionan:
    mejor = min(funcionan, key=rango)
    print(f"\nMejor modelo que responde: {mejor}  (keys {funcionan[mejor]})")
    print("Ponlo en config.yaml como model: openai/" + mejor)
else:
    print("\nNinguna key respondió. ¿Estás en la red de TCS o VPN?")
