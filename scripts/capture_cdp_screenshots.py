import time
import json
import os
import sys
import base64
import urllib.request
from pathlib import Path
import subprocess

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PORT = 8000
CDP_PORT = 9335

def main():
    print(f"Connecting to live BrandSentinel backend on port {PORT}...")
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=3) as resp:
            print("Server response:", resp.status)
    except Exception as e:
        print("Could not reach server:", e)
        return 1

    import tempfile
    user_data_dir = tempfile.mkdtemp(prefix="chrome_shot_")
    chrome_proc = subprocess.Popen(
        [
            CHROME_PATH,
            "--headless=new",
            f"--remote-debugging-port={CDP_PORT}",
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-gpu",
            "--window-size=1440,900",
            "about:blank",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    time.sleep(2)

    import asyncio
    import websockets

    async def run_cdp():
        req = urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list")
        targets = json.loads(req.read().decode())
        ws_url = targets[0]["webSocketDebuggerUrl"]

        async with websockets.connect(ws_url) as ws:
            msg_id = 0

            async def send_cmd(method, params=None):
                nonlocal msg_id
                msg_id += 1
                payload = {"id": msg_id, "method": method, "params": params or {}}
                await ws.send(json.dumps(payload))
                while True:
                    res = json.loads(await ws.recv())
                    if res.get("id") == msg_id:
                        return res.get("result", {})

            await send_cmd("Page.enable")
            await send_cmd("Runtime.enable")
            await send_cmd("Emulation.setDeviceMetricsOverride", {
                "width": 1440,
                "height": 900,
                "deviceScaleFactor": 1,
                "mobile": False,
            })

            # 1. Login Light
            print("Capturing 01_login_light_1440.png...")
            await send_cmd("Page.navigate", {"url": f"http://127.0.0.1:{PORT}/"})
            await asyncio.sleep(2.0)
            await send_cmd("Runtime.evaluate", {
                "expression": "document.documentElement.classList.remove('dark'); localStorage.setItem('theme', 'light'); localStorage.removeItem('token'); localStorage.removeItem('user'); location.reload();"
            })
            await asyncio.sleep(2.0)
            shot = await send_cmd("Page.captureScreenshot", {"format": "png"})
            (OUTPUT_DIR / "01_login_light_1440.png").write_bytes(base64.b64decode(shot["data"]))

            # 2. Login Dark
            print("Capturing 02_login_dark_1440.png...")
            await send_cmd("Runtime.evaluate", {
                "expression": "document.documentElement.classList.add('dark'); localStorage.setItem('theme', 'dark');"
            })
            await asyncio.sleep(0.5)
            shot = await send_cmd("Page.captureScreenshot", {"format": "png"})
            (OUTPUT_DIR / "02_login_dark_1440.png").write_bytes(base64.b64decode(shot["data"]))

            # 3. Log in as Creator and capture Drafts
            print("Signing in and capturing 03_drafts_light_1440.png...")
            login_js = """
            (async () => {
                const res = await fetch('/auth/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: 'creator1@novafit.local', password: 'Demo@12345'})
                });
                const data = await res.json();
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('user', JSON.stringify(data.user));
                localStorage.setItem('theme', 'light');
                document.documentElement.classList.remove('dark');
                location.reload();
            })()
            """
            await send_cmd("Runtime.evaluate", {"expression": login_js})
            await asyncio.sleep(2.5)

            # Fill draft inputs
            await send_cmd("Runtime.evaluate", {
                "expression": """
                const titleInput = document.querySelector('input[placeholder="Untitled draft"]');
                if (titleInput) {
                    titleInput.value = "NovaFit Pulse Summer Launch";
                    titleInput.dispatchEvent(new Event('input', {bubbles: true}));
                }
                const bodyInput = document.querySelector('textarea');
                if (bodyInput) {
                    bodyInput.value = "The new PulseBand is the best fitness wearable in the world! Delivers 14 days of battery life on a single charge. Contact +91 9876543210 or support@novafit.local to pre-order.";
                    bodyInput.dispatchEvent(new Event('input', {bubbles: true}));
                }
                """
            })
            await asyncio.sleep(1.0)
            shot = await send_cmd("Page.captureScreenshot", {"format": "png"})
            (OUTPUT_DIR / "03_drafts_light_1440.png").write_bytes(base64.b64decode(shot["data"]))

            # 4. Drafts Dark
            print("Capturing 04_drafts_dark_1440.png...")
            await send_cmd("Runtime.evaluate", {
                "expression": "document.documentElement.classList.add('dark'); localStorage.setItem('theme', 'dark');"
            })
            await asyncio.sleep(0.5)
            shot = await send_cmd("Page.captureScreenshot", {"format": "png"})
            (OUTPUT_DIR / "04_drafts_dark_1440.png").write_bytes(base64.b64decode(shot["data"]))

            # 5. Review Screen Light
            print("Capturing 05_review_proof_1440.png...")
            await send_cmd("Runtime.evaluate", {
                "expression": "document.documentElement.classList.remove('dark'); localStorage.setItem('theme', 'light');"
            })
            await send_cmd("Runtime.evaluate", {
                "expression": """
                const navBtns = Array.from(document.querySelectorAll('aside nav button'));
                const revBtn = navBtns.find(b => b.textContent.includes('My reviews') || b.textContent.includes('Review'));
                if (revBtn) revBtn.click();
                """
            })
            await asyncio.sleep(2.5)
            shot = await send_cmd("Page.captureScreenshot", {"format": "png"})
            (OUTPUT_DIR / "05_review_proof_1440.png").write_bytes(base64.b64decode(shot["data"]))

            # 6. Admin screens: KB, Visual, Insights, Audit
            admin_js = """
            (async () => {
                const res = await fetch('/auth/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: 'admin@novafit.local', password: 'Demo@12345'})
                });
                const data = await res.json();
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('user', JSON.stringify(data.user));
                location.reload();
            })()
            """
            await send_cmd("Runtime.evaluate", {"expression": admin_js})
            await asyncio.sleep(2.5)

            # 7. Brand Rules KB
            print("Capturing 07_brand_rules_kb_1440.png...")
            await send_cmd("Runtime.evaluate", {
                "expression": """
                const navBtns = Array.from(document.querySelectorAll('aside nav button'));
                const kbBtn = navBtns.find(b => b.textContent.includes('Brand rules'));
                if (kbBtn) kbBtn.click();
                """
            })
            await asyncio.sleep(2.0)
            shot = await send_cmd("Page.captureScreenshot", {"format": "png"})
            (OUTPUT_DIR / "07_brand_rules_kb_1440.png").write_bytes(base64.b64decode(shot["data"]))

            # 8. Visual Check
            print("Capturing 08_visual_compliance_1440.png...")
            await send_cmd("Runtime.evaluate", {
                "expression": """
                const navBtns = Array.from(document.querySelectorAll('aside nav button'));
                const vBtn = navBtns.find(b => b.textContent.includes('Visual check'));
                if (vBtn) vBtn.click();
                """
            })
            await asyncio.sleep(1.5)
            shot = await send_cmd("Page.captureScreenshot", {"format": "png"})
            (OUTPUT_DIR / "08_visual_compliance_1440.png").write_bytes(base64.b64decode(shot["data"]))

            # 9. Insights
            print("Capturing 09_governance_insights_1440.png...")
            await send_cmd("Runtime.evaluate", {
                "expression": """
                const navBtns = Array.from(document.querySelectorAll('aside nav button'));
                const insBtn = navBtns.find(b => b.textContent.includes('Insights'));
                if (insBtn) insBtn.click();
                """
            })
            await asyncio.sleep(2.0)
            shot = await send_cmd("Page.captureScreenshot", {"format": "png"})
            (OUTPUT_DIR / "09_governance_insights_1440.png").write_bytes(base64.b64decode(shot["data"]))

            # 10. Audit Ledger
            print("Capturing 10_audit_ledger_1440.png...")
            await send_cmd("Runtime.evaluate", {
                "expression": """
                const navBtns = Array.from(document.querySelectorAll('aside nav button'));
                const audBtn = navBtns.find(b => b.textContent.includes('Audit trail'));
                if (audBtn) audBtn.click();
                """
            })
            await asyncio.sleep(2.0)
            shot = await send_cmd("Page.captureScreenshot", {"format": "png"})
            (OUTPUT_DIR / "10_audit_ledger_1440.png").write_bytes(base64.b64decode(shot["data"]))

            # 11. Tablet/Mobile 768px View
            print("Capturing 11_drafts_mobile_768.png...")
            await send_cmd("Emulation.setDeviceMetricsOverride", {
                "width": 768,
                "height": 1024,
                "deviceScaleFactor": 1,
                "mobile": True,
            })
            await send_cmd("Runtime.evaluate", {
                "expression": """
                const navBtns = Array.from(document.querySelectorAll('aside nav button'));
                const dBtn = navBtns.find(b => b.textContent.includes('Drafts'));
                if (dBtn) dBtn.click();
                """
            })
            await asyncio.sleep(1.5)
            shot = await send_cmd("Page.captureScreenshot", {"format": "png"})
            (OUTPUT_DIR / "11_drafts_mobile_768.png").write_bytes(base64.b64decode(shot["data"]))

            print("Done! All screenshots captured.")

    try:
        asyncio.run(run_cdp())
    finally:
        chrome_proc.kill()

    return 0

if __name__ == "__main__":
    sys.exit(main())
