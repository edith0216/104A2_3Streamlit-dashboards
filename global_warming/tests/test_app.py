from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def test_app_renders(monkeypatch) -> None:
    monkeypatch.setenv("DASHBOARD_SAMPLE_MODE", "1")

    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()

    assert not app.exception

    assert (app.title[0].value == "Global CO2 Emissions Trends and Drivers")


def test_global_year_filter(monkeypatch) -> None:
    monkeypatch.setenv("DASHBOARD_SAMPLE_MODE", "1")

    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()

    assert not app.exception

    app.slider[0].set_value((2000, 2025)).run()

    assert not app.exception

    assert any(
        "Selected years: 2000-2025"
        in item.value
        for item in app.markdown)