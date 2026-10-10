import copy
from types import SimpleNamespace

import pytest

import pipeline

GOOD = {
    "photo_quality": {"usable": True, "issues": []},
    "identification": {"denomination": "1 cent", "series": "Lincoln Wheat Cent", "year": 1955,
                       "mint_mark": "", "confidence": 0.9},
    "strike_type": {"value": "business", "confidence": 0.8, "evidence": "no mirrored fields"},
    "error_check": {"type": "doubled_die", "confidence": 0.5, "evidence": "doubling on date", "needs_expert": False},
    "grade": {"low": 40, "high": 55, "confidence": 0.5, "basis": "wear on cheek"},
    "notes": "",
}


class FakeClient:
    def __init__(self, payload):
        block = SimpleNamespace(type="tool_use", input=payload)
        self.messages = SimpleNamespace(create=lambda **kw: SimpleNamespace(content=[block]))


@pytest.fixture
def img(tmp_path):
    p = tmp_path / "c.jpg"
    p.write_bytes(b"\xff\xd8\xff\xd9")
    return str(p)


def test_low_confidence_error_is_downgraded(img):
    rep = pipeline.analyze([img], client=FakeClient(copy.deepcopy(GOOD)))
    assert rep.raw["error_check"]["type"] == "unsure"
    assert "error_needs_expert" in rep.flags and "grade_range_wide" in rep.flags


def test_unusable_photo_short_circuits(img):
    bad = copy.deepcopy(GOOD)
    bad["photo_quality"]["usable"] = False
    assert pipeline.analyze([img], client=FakeClient(bad)).flags == ["photo_unusable"]


def test_schema_violation_raises(img):
    bad = copy.deepcopy(GOOD)
    bad["error_check"]["type"] = "made_up"
    with pytest.raises(Exception):
        pipeline.analyze([img], client=FakeClient(bad))


def test_catalog_miss_flagged(img):
    rep = pipeline.analyze([img], client=FakeClient(copy.deepcopy(GOOD)), catalog_lookup=lambda i: None)
    assert "not_in_catalog" in rep.flags
