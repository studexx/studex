do $$
begin
  if exists (
    select 1
    from pg_tables
    where schemaname = 'public'
      and tablename = 'articles'
  ) and not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'articles'
      and policyname = 'articles_delete_anon'
  ) then
    create policy articles_delete_anon
      on public.articles
      for delete
      to anon
      using (true);
  end if;

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
