-- Keep trained model artifacts in a private Supabase Storage bucket.
-- Backend access uses the server-only service role key.
INSERT INTO storage.buckets (id, name, public)
VALUES ('model-artifacts', 'model-artifacts', false)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    public = false;
