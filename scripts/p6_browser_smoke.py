"""P6C real Chromium local browser: select CSV, click, download, verify ZIP."""
from __future__ import annotations

from contextlib import contextmanager
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen
from zipfile import ZipFile

from scripts.p6e6_delivery_policy import verify_shipping_zip

import pandas as pd
from playwright.sync_api import sync_playwright


URL = "http://127.0.0.1:8765"


@contextmanager
def app_server():
    env = dict(os.environ)
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app",
         "--host", "127.0.0.1", "--port", "8765", "--log-level", "warning"],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    try:
        for attempt in range(90):
            if proc.poll() is not None:
                raise RuntimeError("Local test server exited early.")
            try:
                with urlopen(f"{URL}/health", timeout=1) as check:
                    if check.status == 200:
                        break
            except Exception:
                time.sleep(.25)
        else:
            raise RuntimeError("Local server failed health check.")
        yield
    finally:
        proc.terminate()
        try:
            proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate(timeout=5)


def make_demo(path: Path):
    n=120
    demo=pd.DataFrame({
        "날짜": pd.date_range("2026-01-01", periods=n).strftime("%Y-%m-%d"),
        "지역": ["A", "B", "C"] * (n//3),
        "방문수": [20+i%19 for i in range(n)],
        "매출": [float(150+7*(i%19)+i%5) for i in range(n)],
        "비용": [float(80+4*(i%19)+i%7) for i in range(n)],
        "구매": [i%2 for i in range(n)],
    })
    demo.loc[5:17,"지역"]=None
    demo.to_csv(path,index=False,encoding="utf-8-sig")


def check_zip(path: Path, tier: str):
    assert path.stat().st_size > 10_000
    shipping = verify_shipping_zip(path.read_bytes(), tier)
    assert shipping["tier"] == tier
    with ZipFile(path) as z:
        assert z.testzip() is None
        assert z.read("report.pdf").startswith(b"%PDF-")
        assert "manifest.json" in z.namelist()
        m=json.loads(z.read("manifest.json"))
        assert m.get("no_raw_dataset") is True
        assert all(z.read(f["path"]) for f in m["files"])
        if tier != "BASIC":
            assert "model_scores.csv" in z.namelist()
        if tier == "PREMIUM":
            assert "predict.cmd" in z.namelist()
            assert "model_pipeline.skops" in z.namelist()
    print(f"Chromium {tier}: file chooser, actual click, ZIP bytes verified ({path.stat().st_size} bytes)", flush=True)


def main():
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)
        csv=path/"browser_synthetic.csv"
        make_demo(csv)
        with app_server(), sync_playwright() as play:
            browser=play.chromium.launch(headless=True)
            context=browser.new_context(accept_downloads=True)
            try:
                for tier,page in (
                    ("BASIC","basic-mvp"),
                    ("STANDARD","standard-mvp"),
                    ("PREMIUM","premium-mvp"),
                ):
                    tab=context.new_page()
                    tab.set_default_timeout(120_000)
                    tab.goto(f"{URL}/{page}",wait_until="domcontentloaded")
                    assert tab.title() or tab.locator("h1").count()
                    tab.locator('input[type="file"]').set_input_files(str(csv))
                    if tier!="BASIC":
                        tab.locator('input[name="target_column"]').fill("구매")
                        tab.locator('select[name="task_type"]').select_option("classification")
                    with tab.expect_download(timeout=120_000) as info:
                        tab.locator('button[type="submit"]').click()
                    down=info.value
                    destination=path/f"{tier.lower()}_result.zip"
                    down.save_as(destination)
                    check_zip(destination,tier)
                    assert "ZIP" in tab.locator('[role="status"]').inner_text()
                    tab.close()
            finally:
                context.close()
                browser.close()


if __name__ == "__main__":
    main()
