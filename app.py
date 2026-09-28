import os
import re
import math
from datetime import datetime

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    gspread = None
    Credentials = None


def clamp(value, low, high):
    return max(low, min(high, value))


def loan_eligibility(data):
    income = float(data.get("income", 0) or 0)
    age = int(data.get("age", 0) or 0)
    credit_score = int(data.get("credit_score", 0) or 0)
    employment = str(data.get("employment", "Salaried")).strip()

    # Demo scoring model for educational/project purposes.
    income_score = clamp(income / 100000 * 30, 0, 30)
    credit_score_points = clamp((credit_score - 300) / 600 * 40, 0, 40)
    age_points = 15 if 21 <= age <= 55 else (8 if 18 <= age <= 60 else 0)
    employment_points = {
        "Salaried": 15,
        "Self-employed": 13,
        "Business": 12,
        "Professional": 14,
        "Student": 5,
        "Unemployed": 0,
    }.get(employment, 8)

    total = round(income_score + credit_score_points + age_points + employment_points, 1)
    eligible = total >= 55 and credit_score >= 600 and income >= 15000 and 18 <= age <= 60

    if total >= 80:
        band = "High"
    elif total >= 65:
        band = "Moderate"
    elif total >= 55:
        band = "Borderline"
    else:
        band = "Low"

    # Approximate demo loan range; not a lender decision.
    monthly_income = income / 12
    max_emi = monthly_income * (0.40 if credit_score >= 700 else 0.35)
    rate = 10.5 if credit_score >= 750 else (12 if credit_score >= 650 else 14)
    months = 60
    r = rate / 1200
    loan_amount = max_emi * ((1 + r) ** months - 1) / (r * (1 + r) ** months) if r else max_emi * months
    loan_amount = round(max(0, loan_amount), -3)

    reasons = []
    if credit_score < 650:
        reasons.append("Credit score is below the preferred range for many lenders.")
    if income < 25000:
        reasons.append("Higher documented income can improve affordability.")
    if age < 21 or age > 55:
        reasons.append("Age is outside the model's preferred range.")
    if employment in ("Unemployed", "Student"):
        reasons.append("Stable documented employment/income may strengthen an application.")
    if not reasons:
        reasons.append("Inputs meet the demo model's main thresholds.")

    return {
        "eligible": eligible,
        "score": total,
        "band": band,
        "estimated_loan_amount": loan_amount,
        "estimated_max_emi": round(max_emi),
        "interest_assumption": rate,
        "reasons": reasons,
        "disclaimer": "This is a project/demo estimate, not a bank or lender approval."
    }


def credit_analysis(score):
    score = int(score)
    if score >= 800:
        rating = "Exceptional"
    elif score >= 750:
        rating = "Very Good"
    elif score >= 700:
        rating = "Good"
    elif score >= 650:
        rating = "Fair"
    elif score >= 600:
        rating = "Needs Improvement"
    else:
        rating = "Low"

    factors = []
    if score < 700:
        factors.append("Pay EMIs and card bills on time.")
        factors.append("Keep credit utilization comfortably below the limit.")
        factors.append("Avoid applying for many new credit accounts at once.")
    else:
        factors.append("Continue timely repayments.")
        factors.append("Monitor utilization and review your credit report periodically.")

    return {
        "score": score,
        "rating": rating,
        "factors": factors,
        "risk": "Lower" if score >= 700 else ("Moderate" if score >= 650 else "Higher"),
        "disclaimer": "Credit-score guidance is educational and does not replace an official credit report."
    }


def emi_calculation(principal, annual_rate, months):
    principal = float(principal)
    annual_rate = float(annual_rate)
    months = int(months)
    if principal <= 0 or months <= 0:
        raise ValueError("Principal and tenure must be positive.")
    r = annual_rate / 1200
    if r == 0:
        emi = principal / months
    else:
        emi = principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
    total = emi * months
    interest = total - principal
    return {
        "emi": round(emi, 2),
        "total_payment": round(total, 2),
        "total_interest": round(interest, 2),
        "principal": round(principal, 2),
        "months": months,
        "annual_rate": annual_rate
    }


def save_to_google_sheets(record):
    """Optional integration. Set GOOGLE_SERVICE_ACCOUNT_JSON and GOOGLE_SHEET_ID."""
    if not gspread or not Credentials:
        return {"saved": False, "message": "Google Sheets libraries are not installed."}

    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not raw or not sheet_id:
        return {"saved": False, "message": "Google Sheets integration is not configured."}

    try:
        info = json.loads(raw)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(sheet_id)
        ws = sh.sheet1
        ws.append_row([
            datetime.utcnow().isoformat(),
            record.get("income", ""),
            record.get("age", ""),
            record.get("credit_score", ""),
            record.get("employment", ""),
            record.get("result", ""),
        ])
        return {"saved": True, "message": "Record saved to Google Sheets."}
    except Exception as exc:
        return {"saved": False, "message": f"Sheets save failed: {exc}"}


def ask_claude(prompt):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or Anthropic is None:
        return (
            "Claude integration is not configured. Add ANTHROPIC_API_KEY in Render "
            "Environment Variables to enable AI financial guidance. Meanwhile, use "
            "the built-in calculators and educational tips on this page."
        )
    try:
        client = Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
            max_tokens=500,
            system=(
                "You are a cautious financial education assistant. Give general "
                "educational information, not personalized financial advice. "
                "Never claim to approve a loan or guarantee an outcome."
            ),
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in msg.content if hasattr(block, "text"))
    except Exception as exc:
        return f"AI assistant is temporarily unavailable: {exc}"


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "AI Loan Eligibility Checker"})


@app.post("/api/eligibility")
def api_eligibility():
    data = request.get_json(force=True)
    try:
        result = loan_eligibility(data)
        if data.get("save_record"):
            record = dict(data)
            record["result"] = "Eligible" if result["eligible"] else "Review"
            result["sheets"] = save_to_google_sheets(record)
        return jsonify(result)
    except (ValueError, TypeError) as exc:
        return jsonify({"error": f"Please enter valid values: {exc}"}), 400


@app.post("/api/credit-score")
def api_credit():
    data = request.get_json(force=True)
    try:
        return jsonify(credit_analysis(data.get("credit_score", 0)))
    except (ValueError, TypeError) as exc:
        return jsonify({"error": f"Invalid credit score: {exc}"}), 400


@app.post("/api/emi")
def api_emi():
    data = request.get_json(force=True)
    try:
        return jsonify(emi_calculation(
            data.get("principal", 0),
            data.get("rate", 0),
            data.get("months", 0),
        ))
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/ai")
def api_ai():
    data = request.get_json(force=True)
    prompt = str(data.get("prompt", "")).strip()
    if not prompt:
        return jsonify({"error": "Enter a question first."}), 400
    return jsonify({"answer": ask_claude(prompt)})


@app.post("/api/tips")
def api_tips():
    return jsonify({
        "tips": [
            "Pay EMIs and credit-card bills on time.",
            "Keep your credit utilization under control.",
            "Compare total loan cost, not just the advertised interest rate.",
            "Maintain an emergency fund before taking on large debt.",
            "Read processing fees, foreclosure charges and other terms.",
            "Never share OTPs, passwords or card PINs with anyone."
        ]
    })


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Route not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
