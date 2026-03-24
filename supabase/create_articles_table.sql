create table if not exists public.articles (
  id text primary key,
  label text not null default '',
  cat text not null default '',
  level text not null default '',
  orig text not null default '',
  alias text not null default '',
  def text not null default '',
  parent text null,
  children jsonb not null default '[]'::jsonb,
  updated_at timestamptz not null default now()
);

alter table public.articles enable row level security;

do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'articles'
      and policyname = 'articles_select_anon'
  ) then
    create policy articles_select_anon
      on public.articles
      for select
      to anon
      using (true);
  end if;

  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'articles'
      and policyname = 'articles_insert_anon'
  ) then
    create policy articles_insert_anon
      on public.articles
      for insert
      to anon
      with check (true);
  end if;

  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'articles'
      and policyname = 'articles_update_anon'
  ) then
    create policy articles_update_anon
      on public.articles
      for update
      to anon
      using (true)
      with check (true);
  end if;

  if not exists (
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
end $$;

create index if not exists articles_cat_idx on public.articles (cat);
create index if not exists articles_level_idx on public.articles (level);
create index if not exists articles_parent_idx on public.articles (parent);
