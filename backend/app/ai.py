from __future__ import annotations

import json
import logging
import random
from datetime import datetime
from typing import Any, Dict

from fastapi import HTTPException, status
from openai import OpenAI

from .config import get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are the narrative engine for a lightweight text adventure called MindCraft. "
    "Always answer in strict JSON with the keys: world_description, scenario_text, "
    "hints_for_image. The setting must feel cohesive, adventurous, and react to the "
    "player input you receive. Keep each field under 200 words and ensure hints_for_image "
    "remains a short comma-separated list of visual cues."
)


def _create_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(api_key=settings.openai_api_key)


def _build_user_prompt(description: str | None, player_name: str | None) -> str:
    intro = (
        "The player requested a brand-new random world. Invent something bold and distinct."
        if not description
        else "The player described the world seed below. Expand it into a vivid reality."
    )
    focus = (
        "Respect the provided details but feel free to add new twists that match the tone."
        if description
        else "Surprise the player with an imaginative genre mashup that still feels coherent."
    )
    persona = f"The player name (if mentioned) is: {player_name}." if player_name else ""
    seed = f"World seed: {description}" if description else "World seed: <random>"
    request = (
        "Return JSON with world_description, scenario_text, hints_for_image. "
        "scenario_text must pose a hook, dilemma, or event that invites action."
    )
    return " \n".join(filter(None, [intro, focus, persona, seed, request]))


def _parse_payload(raw_text: str) -> Dict[str, Any]:
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse model response: %s", raw_text)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI response malformed") from exc

    required = {"world_description", "scenario_text"}
    missing = required - data.keys()
    if missing:
        logger.error("Model response missing keys: %s | payload=%s", missing, data)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI response incomplete")
    return data


def _mock_world(description: str | None, player_name: str | None) -> Dict[str, Any]:
    """Offline-friendly fallback so the prototype works without OpenAI access."""

    starter_worlds = [
        "Мир парящих островов, связанных кристаллами гравитации.",
        "Постапокалиптический мегаполис, где остатки ИИ управляют погодой.",
        "Город-лабиринт внутри спящего титана, каждая улица — нерв его памяти.",
        "Космическая станция у границы туманности, где время течёт по спирали.",
    ]
    starter_scenarios = [
        "Ты стоишь у портала, который собирается схлопнуться. Нужно решить: прыгать или удерживать его.",
        "Перед тобой консоль древнего ядра, требующая жертвы: воспоминание или силу.",
        "Из глубин слышен зов существа, обещающего помощь за клятву верности.",
        "Сын ветра просит сопроводить его через запрещённый сектор, где каждый шаг меняет прошлое.",
    ]
    starter_hints = [
        "неоновые огни, туманность, тёмное небо",
        "парящие острова, кристаллы, тёплый закат",
        "киберпанк город, дождь, отражения",
        "древний храм, биолюминесцентные растения",
    ]

    seed_world = description.strip() if description else random.choice(starter_worlds)
    hero = player_name or random.choice(["Рина", "Касс", "Эллар", "Сорен"])
    scenario = random.choice(starter_scenarios)
    hint = random.choice(starter_hints)

    timestamp = datetime.utcnow().strftime("%H:%M:%S")

    return {
        "world_description": f"{seed_world} (mock {timestamp})",
        "scenario_text": f"{hero} оказывается в ситуации: {scenario}",
        "hints_for_image": hint,
        "player_name": hero,
    }


def generate_world(description: str | None, player_name: str | None) -> Dict[str, Any]:
    settings = get_settings()

    if not settings.use_live_ai:
        return _mock_world(description, player_name)

    prompt = _build_user_prompt(description, player_name)
    logger.debug("MindCraft prompt: %s", prompt)

    client = _create_client()

    try:
        response = client.responses.create(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": [{"type": "text", "text": SYSTEM_PROMPT}]},
                {"role": "user", "content": [{"type": "text", "text": prompt}]},
            ],
            temperature=0.9,
        )
    except Exception as exc:  # fallback to mock when OpenAI is unavailable
        logger.exception("OpenAI request failed; falling back to mock payload")
        return _mock_world(description, player_name)

    try:
        raw_text = response.output[0].content[0].text
    except (AttributeError, IndexError, KeyError) as exc:
        logger.exception("Unexpected response structure: %s", response)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI response unreadable") from exc

    payload = _parse_payload(raw_text)
    payload.setdefault("hints_for_image", None)
    if player_name:
        payload["player_name"] = player_name
    return payload
