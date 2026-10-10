"""Output contract for the coin pipeline. Any front end (CAD/cloud builder, web, mobile) consumes this JSON."""

ERROR_TYPES = [
    "none", "doubled_die", "repunched_mint_mark", "off_center", "clipped_planchet",
    "broadcast_strike", "die_crack_or_cud", "wrong_planchet", "double_strike",
    "machine_doubling", "strike_doubling", "post_mint_damage", "unsure",
]

# Forced tool call => the API returns arguments that conform to this schema.
COIN_REPORT_TOOL = {
    "name": "report_coin",
    "description": "Report what is visible on the coin photos. Use null / 'unsure' rather than guessing.",
    "input_schema": {
        "type": "object",
        "required": ["photo_quality", "identification", "strike_type", "error_check", "grade", "notes"],
        "properties": {
            "photo_quality": {
                "type": "object",
                "required": ["usable", "issues"],
                "properties": {
                    "usable": {"type": "boolean"},
                    "issues": {"type": "array", "items": {"type": "string"},
                               "description": "e.g. blur, glare, slab_reflection, cropped, only_one_side"},
                },
            },
            "identification": {
                "type": "object",
                "required": ["denomination", "series", "year", "mint_mark", "confidence"],
                "properties": {
                    "denomination": {"type": ["string", "null"]},
                    "series": {"type": ["string", "null"], "description": "e.g. Lincoln Wheat Cent"},
                    "year": {"type": ["integer", "null"]},
                    "mint_mark": {"type": ["string", "null"], "description": "'' if none is visible, null if unreadable"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
            "strike_type": {
                "type": "object",
                "required": ["value", "confidence", "evidence"],
                "properties": {
                    "value": {"enum": ["business", "proof", "unsure"]},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "evidence": {"type": "string", "description": "mirrored fields, frosted devices, etc."},
                },
            },
            "error_check": {
                "type": "object",
                "required": ["type", "confidence", "evidence", "needs_expert"],
                "properties": {
                    "type": {"enum": ERROR_TYPES},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "evidence": {"type": "string",
                                 "description": "Where on the coin, and why it is not machine/strike doubling or damage"},
                    "needs_expert": {"type": "boolean"},
                },
            },
            "grade": {
                "type": "object",
                "required": ["low", "high", "confidence", "basis"],
                "properties": {
                    "low": {"type": ["integer", "null"], "minimum": 1, "maximum": 70},
                    "high": {"type": ["integer", "null"], "minimum": 1, "maximum": 70},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "basis": {"type": "string", "description": "wear points, luster, marks observed"},
                },
            },
            "notes": {"type": "string"},
        },
    },
}
