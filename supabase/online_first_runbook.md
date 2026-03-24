# Studex Online-First Runbook

## 1. Create `public.articles`

Open Supabase SQL Editor and run:

```sql
\i create_articles_table.sql
```

If `\i` is not supported in the editor, paste the contents of:

- `supabase/create_articles_table.sql`

and run it directly.

## 2. Finish online-first policies

Run:

- `supabase/online_first_policies.sql`
- `supabase/content_logs_compat.sql`

This adds:

- anon delete policy for `public.articles`
- anon insert policy for `public.content_logs` when that table already exists
- `content_logs.item_kind` compatibility for Studex (`page/article/work/entry`)

## 2.5. Optional legacy cleanup

If your schema still shows unused legacy tables:

- `public.article_logs`
- `public.note_logs`

run:

- `supabase/cleanup_legacy_logs.sql`

This cleanup is safe by default: it only drops those tables when they are empty.

## 3. Verify schema from this workspace

```bash
python3 tests/check_supabase_schema.py
```

Expected result:

- `articles: PASS`
- `content_logs: PASS`

## 4. Reconnect Studex

In Studex command bar:

```text
/retry supabase
```

Optional:

```text
/sync status
```

Expected notice:

- `Sync source: Supabase`

## 5. Smoke test

```bash
python3 tests/smoke_playwright.py
```

All checks should pass.
