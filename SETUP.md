# Setup

The accounts, keys and spend caps behind the demo and the offline tooling. **No secret values
are in this file.** They live in the local `.env` (gitignored) and, where the deployed app needs
them, in Vercel project env. Settings come from [`STACK.md`](STACK.md) and
[`GUARDRAILS.md`](GUARDRAILS.md).

## Accounts

| Service | Resource | Settings |
|---|---|---|
| Supabase | project `ask-the-city` (ref `ncmzxqsgqbntssaxxerq`) | Free, `us-east-1`, `vector` extension in schema `extensions` |
| Vercel | project `ask-the-city` (team `melihonats-projects`) | Next.js, function region `iad1` |
| Vercel AI Gateway | team credit | **$10 prepaid (minimum top-up), auto top-up off**, **$2/month budget alert** (soft cap) |
| Cloudflare R2 | bucket `ask-the-city-raw` | private (no public access, no r2.dev URL), API token scoped to this bucket, read/write |
| Voyage AI | key used only by ingestion | own account limit; not the Gateway's credit |
| Anthropic | key used only by the eval judge | own workspace with a monthly spend limit |

## Environment variables

| Variable | Holds | `.env` | Vercel |
|---|---|:-:|:-:|
| `SUPABASE_URL` | Supabase API URL | ✓ | ✓ |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase secret key (`sb_secret_…`, the service-role equivalent; server only) | ✓ | ✓ |
| `DATABASE_URL` | Postgres connection string, for ingestion and migrations | ✓ | |
| `AI_GATEWAY_API_KEY` | AI Gateway key for local runs; deployments use Vercel OIDC | ✓ | |
| `VOYAGE_API_KEY` | Voyage key, **ingestion only** | ✓ | |
| `JUDGE_ANTHROPIC_API_KEY` | Anthropic key, **eval judge only**. Not named `ANTHROPIC_API_KEY`, so no SDK picks it up by default | ✓ | |
| `R2_ACCOUNT_ID` | Cloudflare account id for the R2 endpoint | ✓ | |
| `R2_ACCESS_KEY_ID` | R2 API token access key | ✓ | |
| `R2_SECRET_ACCESS_KEY` | R2 API token secret | ✓ | |
| `R2_BUCKET` | `ask-the-city-raw` | ✓ | |
| `EVAL_HEADER_SECRET` | value of the eval header ([`GUARDRAILS.md`](GUARDRAILS.md#the-eval-header)) | ✓ | ✓ |
| `IP_HASH_SALT` | salt for the per-IP hash in `usage_daily` | ✓ | ✓ |
| `CRON_SECRET` | guards `/api/keepalive`; Vercel sends it as `Authorization: Bearer` on crons | ✓ | ✓ |

Vercel env vars are `sensitive` and target Production and Preview; `.env` covers local runs.
`vercel link` also writes `.env.local` with a short-lived `VERCEL_OIDC_TOKEN`
(`vercel env pull` refreshes it), which can stand in for `AI_GATEWAY_API_KEY` locally.

The three app secrets are random (48 characters). To rotate one, generate a new value, update
`.env` and Vercel env, then redeploy. A new `IP_HASH_SALT` resets the per-IP daily counts.
