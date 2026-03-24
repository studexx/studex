alter table if exists public.content_logs enable row level security;

do $$
begin
  if exists (
    select 1
    from information_schema.table_constraints
    where table_schema = 'public'
      and table_name = 'content_logs'
      and constraint_name = 'content_logs_item_kind_check'
  ) then
    alter table public.content_logs
      drop constraint content_logs_item_kind_check;
  end if;
exception
  when undefined_table then
    null;
end $$;

do $$
begin
  if exists (
    select 1
    from information_schema.tables
    where table_schema = 'public'
      and table_name = 'content_logs'
  ) then
    alter table public.content_logs
      add constraint content_logs_item_kind_check
      check (item_kind in ('page', 'article', 'work', 'entry'));
  end if;
exception
  when duplicate_object then
    null;
end $$;

do $$
begin
  if exists (
    select 1
    from pg_tables
    where schemaname = 'public'
      and tablename = 'content_logs'
  ) and not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'content_logs'
      and policyname = 'content_logs_insert_anon'
  ) then
    create policy content_logs_insert_anon
      on public.content_logs
      for insert
      to anon
      with check (true);
  end if;
end $$;
