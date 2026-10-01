-- Backend-only tables: the server uses the Supabase secret/service role key.
-- Keep direct browser access disabled unless explicit RLS policies are added.

alter table public.learning_events enable row level security;
revoke all privileges on table public.learning_events from anon, authenticated;
grant all privileges on table public.learning_events to service_role;
grant usage, select on sequence public.learning_events_id_seq to service_role;

alter table public.model_versions enable row level security;
revoke all privileges on table public.model_versions from anon, authenticated;
grant all privileges on table public.model_versions to service_role;
grant usage, select on sequence public.model_versions_id_seq to service_role;

alter table public.predictions enable row level security;
revoke all privileges on table public.predictions from anon, authenticated;
grant all privileges on table public.predictions to service_role;
grant usage, select on sequence public.predictions_id_seq to service_role;

alter table public.news_items enable row level security;
revoke all privileges on table public.news_items from anon, authenticated;
grant all privileges on table public.news_items to service_role;
grant usage, select on sequence public.news_items_id_seq to service_role;
