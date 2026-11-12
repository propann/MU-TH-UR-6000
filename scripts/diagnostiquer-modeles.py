#!/usr/bin/env python3
"""Sondes Ollama locales, sans notes personnelles et sans API facturable."""
import argparse
import json
import time
import urllib.request


def request(path, payload=None):
    raw = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        "http://127.0.0.1:11434" + path, data=raw,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", nargs="*", help="Par défaut, tous les modèles installés")
    args = parser.parse_args()
    models = args.models or [item["name"] for item in request("/api/tags").get("models", [])]
    questions = [
        ("instruction", "Réponds uniquement par TEST IA OK", "TEST IA OK"),
        ("calcul", "Combien font 17 multiplié par 6 ?", "102"),
        ("contexte", "Document fourni : le projet SAPHIR écoute sur le port 43219. Quel port utilise SAPHIR ?", "43219"),
    ]
    for model in models:
        for label, question, expected in questions:
            start = time.monotonic()
            try:
                result = request("/api/chat", {
                    "model": model, "stream": False,
                    "messages": [
                        {"role": "system", "content": "Réponds en français, précisément et brièvement. N'invente rien."},
                        {"role": "user", "content": question}],
                    "options": {"temperature": 0.2, "num_predict": 2048}})
                message = result.get("message", {})
                answer = message.get("content", "")
                print(json.dumps({
                    "model": model, "test": label,
                    "expected_present": expected in answer,
                    "answer": answer, "thinking_present": bool(message.get("thinking")),
                    "done_reason": result.get("done_reason"),
                    "tokens": result.get("eval_count"),
                    "seconds": round(time.monotonic() - start, 2)}, ensure_ascii=False), flush=True)
            except Exception as error:
                print(json.dumps({"model": model, "test": label, "error": str(error)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
