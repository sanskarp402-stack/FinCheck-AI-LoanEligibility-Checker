# FinCheck AI — Loan Eligibility Checker

AI-powered BFSI financial-services demo built with **Python, Flask, HTML, CSS and JavaScript**.

## Features

- Loan Eligibility Checker
- Credit Score Analyzer
- EMI Calculator
- Financial Tips
- Optional Anthropic Claude AI assistant
- Optional Google Sheets record storage
- Responsive glassmorphism UI
- Server-side calculations and validation
- Render deployment configuration
- `/health` endpoint for deployment monitoring

> **Important:** This is an educational/demo application. It is not a lender, bank, credit bureau, financial adviser, or approval engine. The eligibility result is a simplified project model and must not be treated as an actual loan decision.

## Run locally

```bash
python -m venv .venv
```

### Windows
```bash
.venv\Scripts\activate
```

### macOS/Linux
```bash
source .venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
python app.py
```

Open: `http://127.0.0.1:5000`

## GitHub

1. Create a new empty GitHub repository, for example `fincheck-ai`.
2. Upload all files from this folder.
3. Commit to the `main` branch.

Or use:

```bash
git init
git add .
git commit -m "Initial FinCheck AI project"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

## Deploy on Render

### Fast method

1. Push the project to GitHub.
2. Open Render and choose **New → Web Service**.
3. Connect the GitHub repository.
4. Runtime: **Python**
5. Build command:
   `pip install -r requirements.txt`
6. Start command:
   `gunicorn app:app`
7. Deploy.

Render should provide a public URL such as:

`https://fincheck-ai.onrender.com`

The included `render.yaml` can also be used for a Blueprint deployment.

## Enable Claude AI

On Render, add:

- `ANTHROPIC_API_KEY` = your Anthropic API key
- `ANTHROPIC_MODEL` = a model available to your Anthropic account

Do **not** put the API key in GitHub or JavaScript.

## Enable Google Sheets

Create a Google service account and a Google Sheet, then configure:

- `GOOGLE_SERVICE_ACCOUNT_JSON` = the service-account JSON as a single environment-variable value
- `GOOGLE_SHEET_ID` = the ID of the target spreadsheet

Share the Google Sheet with the service account email with appropriate edit permission.

The eligibility form has an optional checkbox to save a demo record.

## API endpoints

- `GET /` — web application
- `GET /health` — health check
- `POST /api/eligibility`
- `POST /api/credit-score`
- `POST /api/emi`
- `POST /api/ai`
- `POST /api/tips`

## Suggested GitHub repository description

> AI-powered BFSI platform for loan eligibility, credit-score analysis, EMI calculation and financial education, built with Flask and a responsive glassmorphism frontend.

## Suggested project presentation points

- Problem: financial decisions are fragmented across different tools.
- Solution: one web platform for eligibility, credit, EMI and educational guidance.
- Frontend: HTML/CSS/JavaScript with responsive glassmorphism UI.
- Backend: Python Flask REST-style endpoints.
- AI: optional Anthropic Claude integration.
- Storage: optional Google Sheets integration.
- Deployment: Render + GitHub.
- Security: environment variables for secrets, server-side calculations and input validation.
