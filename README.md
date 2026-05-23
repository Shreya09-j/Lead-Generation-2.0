# CRM Lead Enrichment Automation

This project turns a CSV of company names into CRM-ready public business contact records.

It reads `companies.csv`, discovers public professional profiles, enriches contacts with configured providers, validates email/phone/profile fields, and writes:

- `leads.csv`
- `failed_companies.csv`
- `processing_logs.txt`

The pipeline is designed for public business data and official enrichment APIs. It does not bypass authentication, paywalls, robots protections, or privacy controls.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
Copy-Item .env.example .env
```

Fill `.env` with the provider credentials you want to use. Missing providers are skipped.

## Input

Create `companies.csv`:

```csv
company
Tesla
OpenAI
Nvidia
```

Optional columns are supported when you already have partial data:

```csv
company,domain,name,title,email,phone,linkedin
```

## Run

```powershell
python outreach_automation.py --input companies.csv
```

Useful options:

```powershell
python outreach_automation.py --input companies.csv --max-contacts 3
python outreach_automation.py --input companies.csv --browser-discovery
python outreach_automation.py --input companies.csv --include-domain
python outreach_automation.py --input companies.csv --offline
```

`--browser-discovery` uses Playwright with paced search behavior to discover public profile results. The default mode uses normal HTTP requests to public pages and provider APIs.

## Output Columns

Default `leads.csv` columns:

```csv
company,name,title,email,phone,linkedin,status
```

Status values:

- `verified`: returned or validated by an enrichment provider
- `guessed`: generated from common business email patterns because no verified email was found
- `not_found`: contact found, but no verified or guessed email was available

Use `--include-domain` to add a `domain` column.

## Provider Waterfall

For each discovered professional, the script tries:

1. RocketReach
2. Lusha
3. Hunter
4. Snov
5. Guessed email patterns, if enabled

The script keeps running when a provider fails or rate limits. Errors are written to `processing_logs.txt`, and companies with no usable contacts are written to `failed_companies.csv`.

## Privacy and Pacing

- Collects only publicly accessible professional/business information.
- Uses random delays and retry backoff.
- Avoids high-frequency page opens.
- Does not scrape private account data or bypass access controls.
- Generated emails are clearly marked as `guessed`.
