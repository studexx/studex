from pathlib import Path
import json
import re
from urllib.parse import quote
from urllib.request import Request, urlopen

from playwright.sync_api import sync_playwright


HTML_PATH = Path(__file__).resolve().parents[1].joinpath("studex_0.10.html")
FILE_URL = HTML_PATH.as_uri()
SMOKE_PREFIX = "smoke_test_page_"


def extract_supa_config() -> tuple[str, str]:
    text = HTML_PATH.read_text()
    url_match = re.search(r"const SUPA_URL='([^']+)';", text)
    key_match = re.search(r"const SUPA_KEY='([^']+)';", text)
    if not url_match or not key_match:
        raise RuntimeError("Supabase config not found in studex_0.10.html")
    return url_match.group(1), key_match.group(1)


def cleanup_smoke_pages() -> None:
    supa_url, supa_key = extract_supa_config()
    query = (
        "or=("
        f"id.like.{SMOKE_PREFIX}%25,"
        "id.like.soft_break_smoke_%25,"
        "id.like.probe_%25,"
        "id.like.save_probe_%25,"
        "label.ilike.*Smoke%20Test%20Page*,"
        "label.ilike.*Soft%20Break%20Smoke*,"
        "label.ilike.*Save%20Probe*,"
        "label.eq.Probe)"
    )
    list_req = Request(
        f"{supa_url}/rest/v1/articles?select=id&{query}",
        headers={
            "apikey": supa_key,
            "Authorization": f"Bearer {supa_key}",
        },
    )
    with urlopen(list_req) as r:
        rows = json.load(r)
    for row in rows:
        delete_req = Request(
            f"{supa_url}/rest/v1/articles?id=eq.{quote(row['id'])}",
            method="DELETE",
            headers={
                "apikey": supa_key,
                "Authorization": f"Bearer {supa_key}",
                "Prefer": "return=minimal",
            },
        )
        with urlopen(delete_req):
            pass


def main() -> int:
    results = []
    console_logs = []
    page_errors = []
    cleanup_smoke_pages()

    def record(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, ok, detail))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 980})
        page.add_init_script(
            """
            (() => {
              localStorage.clear();
              sessionStorage.clear();
            })();
            """
        )
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on(
            "console",
            lambda msg: console_logs.append(f"{msg.type}: {msg.text}")
            if msg.type in ("error", "warning")
            else None,
        )

        page.goto(FILE_URL, wait_until="load")
        page.wait_for_timeout(1000)

        stale_target = page.evaluate(
            """
            (() => {
              const id = Object.keys(DB).find(key => (DB[key]?.def || '').length > 0);
              return id ? {id, label: DB[id].label} : null;
            })()
            """
        )

        page.evaluate(
            f"""
            (() => {{
              const targetId = {stale_target["id"]!r};
              const raw = localStorage.getItem('studex:cache-db-state');
              if (!raw || !targetId) return false;
              const cached = JSON.parse(raw);
              if (!cached?.db?.[targetId]) return false;
              cached.db[targetId].def = '';
              localStorage.setItem('studex:cache-db-state', JSON.stringify(cached));
              localStorage.setItem('studex:supa:articles-unavailable', '1');
              return true;
            }})()
            """
        )
        page.reload(wait_until="load")
        page.wait_for_timeout(1600)
        healed_body = page.evaluate(
            f"""
            (() => ({{
              defLen: DB?.[{stale_target["id"]!r}]?.def?.length || 0,
              sync: typeof syncStatusText === 'function' ? syncStatusText() : ''
            }}))()
            """
        )
        record(
            "stale-flag-auto-heal",
            healed_body["defLen"] > 0 and "Supabase" in healed_body["sync"],
            str(healed_body),
        )

        page.evaluate(
            """
            (() => {
              localStorage.setItem('studex:cache-db-state', JSON.stringify({
                db: {
                  theology: {label:'Theology',cat:'theology',level:'Discipline',orig:'',alias:'',def:'',children:['soft_break_smoke_cached']},
                  soft_break_smoke_cached: {label:'Soft Break Smoke Cached',cat:'General Theology',level:'Topic',orig:'',alias:'',def:'',parent:'theology',children:[]}
                },
                disc: {theology:['Soft Break Smoke Cached']},
                writings: ['Diaries'],
                dirtyIds: ['soft_break_smoke_cached']
              }));
              return true;
            })()
            """
        )
        page.reload(wait_until="load")
        page.wait_for_timeout(1400)
        pruned_artifact = page.evaluate(
            """
            (() => ({
              hasId: !!DB.soft_break_smoke_cached,
              hasLabel: Object.values(DB).some(entry => (entry?.label || '').includes('Soft Break Smoke Cached'))
            }))()
            """
        )
        record(
            "cached-test-artifacts-pruned",
            not pruned_artifact["hasId"] and not pruned_artifact["hasLabel"],
            str(pruned_artifact),
        )
        page.evaluate(
            """
            (() => {
              localStorage.clear();
              sessionStorage.clear();
              return true;
            })()
            """
        )
        page.reload(wait_until="load")
        page.wait_for_timeout(1200)

        record("initial-home", page.locator("#pg-home.on").count() == 1)
        record("initial-tab", "Home" in page.locator("#tab-list").inner_text())

        page.click("button[onclick=\"openNA('knowledge')\"]")
        page.wait_for_timeout(200)
        record("new-page-open", page.locator("#nabg.on").count() == 1)
        page.keyboard.press("Escape")
        page.wait_for_timeout(150)
        record("new-page-close-esc", page.locator("#nabg.on").count() == 0)

        temp_target = page.evaluate(
            """
            (() => {
              const id = `smoke_test_page_${Date.now().toString(36)}`;
              document.getElementById('nat').value = `Smoke Test Page ${Date.now()}`;
              naKind = 'knowledge';
              naLevelValue = 'Branch';
              naLocValue = 'general_theology';
              createItem();
              return { id, labelPrefix: 'Smoke Test Page' };
            })()
            """
        )
        page.wait_for_timeout(1000)
        temp_target = page.evaluate(
            """
            (() => {
              const ids = Object.keys(DB).filter(id => id.startsWith('smoke_test_page_'));
              const id = ids.length ? ids[ids.length - 1] : null;
              return id ? {id, label: DB[id].label} : null;
            })()
            """
        )
        record("temp-page-created", temp_target is not None, str(temp_target))
        page.evaluate(
            f"""
            (() => {{
              openPageItem({temp_target['id']!r});
              saveField({temp_target['id']!r}, 'def', 'Body reload save check');
              flushQueuedSave({temp_target['id']!r});
            }})()
            """
        )
        page.wait_for_timeout(300)
        page.reload(wait_until="load")
        page.wait_for_timeout(1600)
        body_reload_state = page.evaluate(
            f"""
            (() => ({{
              def: DB[{temp_target["id"]!r}]?.def || ''
            }}))()
            """
        )
        record(
            "body-edit-persists-reload",
            body_reload_state["def"] == "Body reload save check",
            str(body_reload_state),
        )

        page.evaluate(
            f"""
            openPageItem({temp_target["id"]!r});
            saveField({temp_target["id"]!r}, 'def', 'Line 1\\nLine 2\\nLine 3');
            """
        )
        page.wait_for_timeout(1700)
        local_save_state = page.evaluate(
            f"""
            ({{
              dirty: DIRTY_IDS.has({temp_target["id"]!r}),
              saveOn: document.getElementById('btn-save').classList.contains('on')
            }})
            """
        )
        record("local-save-clears-dirty", not local_save_state["dirty"], str(local_save_state))
        record("local-save-btn-off", not local_save_state["saveOn"], str(local_save_state))

        page.fill("#cmdk", "/delete page")
        page.keyboard.press("Enter")
        page.wait_for_timeout(900)
        record("trash-delete", not page.evaluate(f"!!DB[{temp_target['id']!r}]"))

        page.fill("#cmdk", "/trash")
        page.keyboard.press("Enter")
        page.wait_for_timeout(200)
        record("trash-picker-open", page.locator("#pkbg.on").count() == 1)
        page.keyboard.press("Escape")
        page.wait_for_timeout(120)
        page.fill("#cmdk", "/restore last")
        page.keyboard.press("Enter")
        page.wait_for_timeout(700)
        record("trash-restore", page.evaluate(f"!!DB[{temp_target['id']!r}]"))

        page.fill("#cmdk", "/delete page")
        page.keyboard.press("Enter")
        page.wait_for_timeout(900)
        page.reload(wait_until="load")
        page.wait_for_timeout(1000)
        record("trash-persists-reload", not page.evaluate(f"!!DB[{temp_target['id']!r}]"))

        browser.close()
    cleanup_smoke_pages()

    print("RESULTS")
    all_ok = True
    for name, ok, detail in results:
        all_ok = all_ok and ok
        print(f"{name}: {'PASS' if ok else 'FAIL'}" + (f" | {detail}" if detail else ""))

    print("PAGE_ERRORS")
    for err in page_errors:
        all_ok = False
        print(err)

    print("CONSOLE_LOGS")
    for err in console_logs:
        print(err)

    return 0 if all_ok and not page_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
