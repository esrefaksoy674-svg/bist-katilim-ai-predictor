create table if not exists public.context_snapshots (
    symbol text not null,
    available_date date not null,
    technical_features jsonb not null default '{}'::jsonb,
    news_features jsonb not null default '{}'::jsonb,
    market_features jsonb not null default '{}'::jsonb,
    sector_features jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    primary key (symbol, available_date)
);

create index if not exists context_snapshots_available_date_idx
    on public.context_snapshots (available_date desc);

alter table public.context_snapshots enable row level security;
revoke all privileges on table public.context_snapshots from anon, authenticated;
grant all privileges on table public.context_snapshots to service_role;
