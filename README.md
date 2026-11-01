# Ask the City

## Operations

Two daily Vercel crons call `/api/keepalive`, which runs a real search with a stored query
embedding, so the free Supabase database never pauses and no AI credit is spent. A daily GitHub
Actions workflow calls `/api/health` and fails, e-mailing the owner, when the database is down.

GitHub disables scheduled workflows after 60 days without a commit. If the DB health check
stops, re-enable it in Actions.
