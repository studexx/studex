from pathlib import Path
import json
import re
import urllib.error
import urllib.parse
import urllib.request


HTML_PATH = Path(__file__).resolve().parents[1] / "studex_0.10.html"


def extract(name: str, text: str) -> str:
    match = re.search(rf"const {name}='([^']+)'", text)
    if not match:
        raise RuntimeError(f"Missing {name} in {HTML_PATH.name}")
    return match.group(1)


def request_json(url: str, key: str):
    req = urllib.request.Request(
        url,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            body = res.read().decode("utf-8")
            return res.status, json.loads(body) if body else None
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8")
        try:
            payload = json.loads(body) if body else None
        except json.JSONDecodeError:
            payload = body
        return err.code, payload


def check_table(base_url: str, key: str, table: str):
    query = urllib.parse.urlencode({"select": "id", "limit": "1"})
    status, payload = request_json(f"{base_url}/rest/v1/{table}?{query}", key)
    ok = status == 200
    return {
        "table": table,
        "ok": ok,
        "status": status,
        "detail": payload,
    }


def main() -> int:
    text = HTML_PATH.read_text()
    supa_url = extract("SUPA_URL", text)
    supa_key = extract("SUPA_KEY", text)

    results = [
        check_table(supa_url, supa_key, "articles"),
        check_table(supa_url, supa_key, "content_logs"),
    ]

    overall_ok = True
    print("SUPABASE_SCHEMA")
    for item in results:
      overall_ok = overall_ok and item["ok"]
      state = "PASS" if item["ok"] else "FAIL"
      print(f"{item['table']}: {state} | status={item['status']} | detail={item['detail']}")

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
