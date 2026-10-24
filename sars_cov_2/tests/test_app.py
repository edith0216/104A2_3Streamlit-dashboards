from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]

def test_app_renders(monkeypatch) -> None:
    monkeypatch.setenv("DASHBOARD_SAMPLE_MODE", "1")

    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()

    assert not app.exception
    assert app.title[0].value == "COVID-19 Mortality Across Selected Countries"


def test_country_filter_and_empty_state(monkeypatch) -> None:
    monkeypatch.setenv("DASHBOARD_SAMPLE_MODE", "1")

    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()

    app.multiselect[0].set_value(["Australia"]).run()

    assert not app.exception
    assert any(
        "Selected: Australia" in item.value
        for item in app.markdown)

    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()

    app.multiselect[0].set_value([]).run()

    assert not app.exception
    assert any(
        "No observations match the selected filters."
        in item.value
        for item in app.info)