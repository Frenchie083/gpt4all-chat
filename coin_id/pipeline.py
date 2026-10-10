"""Coin pipeline backed by a hosted vision model. One call -> structured report -> rule-based checks."""
import base64
import mimetypes
from dataclasses import dataclass, field
from typing import Callable, Optional

from jsonschema import validate

from prompts import SYSTEM, USER
from schema import COIN_REPORT_TOOL

DEFAULT_MODEL = "claude-sonnet-5-5"
ERROR_MIN_CONFIDENCE = 0.75   # below this an error claim is downgraded to 'unsure'
MAX_GRADE_SPREAD = 6          # wider than this => grade is not reported as a point estimate


def _image_block(path: str) -> dict:
    media = mimetypes.guess_type(path)[0] or "image/jpeg"
    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode()
    return {"type": "image", "source": {"type": "base64", "media_type": media, "data": data}}


@dataclass
class Report:
    raw: dict
    flags: list = field(default_factory=list)   # reasons a human should look
    catalog: Optional[dict] = None              # filled by the lookup hook


def analyze(image_paths: list, client=None, model: str = DEFAULT_MODEL,
            catalog_lookup: Optional[Callable[[dict], Optional[dict]]] = None) -> Report:
    """image_paths: obverse first, reverse second. client: anthropic.Anthropic() or a test double."""
    if client is None:
        import anthropic
        client = anthropic.Anthropic()
    content = [_image_block(p) for p in image_paths] + [{"type": "text", "text": USER}]
    resp = client.messages.create(
        model=model, max_tokens=1500, system=SYSTEM,
        tools=[COIN_REPORT_TOOL], tool_choice={"type": "tool", "name": "report_coin"},
        messages=[{"role": "user", "content": content}],
    )
    raw = next(b.input for b in resp.content if getattr(b, "type", "") == "tool_use")
    validate(raw, COIN_REPORT_TOOL["input_schema"])
    return _postprocess(raw, catalog_lookup)


def _postprocess(raw: dict, catalog_lookup) -> Report:
    """Deterministic guardrails applied to the model's answer."""
    rep = Report(raw=raw)
    if not raw["photo_quality"]["usable"]:
        rep.flags.append("photo_unusable")
        return rep

    err = raw["error_check"]
    if err["type"] not in ("none", "unsure") and err["confidence"] < ERROR_MIN_CONFIDENCE:
        rep.flags.append(f"error_downgraded:{err['type']}")
        err["type"], err["needs_expert"] = "unsure", True
    if err["needs_expert"]:
        rep.flags.append("error_needs_expert")

    g = raw["grade"]
    if g["low"] is not None and g["high"] is not None:
        if g["low"] > g["high"]:
            g["low"], g["high"] = g["high"], g["low"]
        if g["high"] - g["low"] > MAX_GRADE_SPREAD:
            rep.flags.append("grade_range_wide")

    ident = raw["identification"]
    if ident["confidence"] < 0.6:
        rep.flags.append("id_low_confidence")
    if catalog_lookup and ident["year"] and ident["denomination"]:
        rep.catalog = catalog_lookup(ident)
        if rep.catalog is None:
            rep.flags.append("not_in_catalog")   # e.g. impossible year/mint-mark combination
    return rep
