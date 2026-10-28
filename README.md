# Shops Like Yours — NEXUS
**Paytm Build for India AI Hackathon | Merchant Growth AI**

A runnable prototype matching the submitted PPT: sales overview, comparison against similar demo merchants, personalized business action, and advertising ideas.

## Important data limitation
This project ships with **synthetic demo data**. It does not connect to Paytm systems and does not contain real competitor data. Do not present the displayed peer benchmarks as real-world facts. Live benchmarking would require authorized, privacy-preserving access to merchant data and consent/security controls.

## Stack
- Frontend: HTML, CSS, JavaScript
- Backend: Python + FastAPI
- Data processing: Pandas, NumPy
- Peer benchmark foundation: scikit-learn listed for the next iteration; current demo uses grouped statistics and transparent rules.

## Run in VS Code (Windows)
1. Extract the ZIP.
2. Open the `Shops_Like_Yours` folder in VS Code.
3. Open Terminal → New Terminal.
4. Create and activate a virtual environment:
   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, run `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` and use that interpreter directly.
5. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
6. Configure OpenAI (optional; without a key, the existing rule-based advice still works):
   ```powershell
   Copy-Item .env.example .env
   notepad .env
   ```
   Set `OPENAI_API_KEY` in `.env` to your own active OpenAI API key. Keep `.env` private; it is ignored by Git. Never put API keys in frontend files or commit them.
7. Start the API from the project root:
   ```powershell
   uvicorn app.main:app --reload
   ```
8. Open `frontend/index.html` in a browser, or use VS Code Live Server. Keep the API running.
9. API documentation: http://127.0.0.1:8000/docs

## Demo walkthrough
- Select a shop category and area.
- Review sales metrics and the daily sales chart.
- Enter your shop's daily sales and compare against the synthetic peer group.
- Generate a personalized action and advertising idea in English or Hindi. When `OPENAI_API_KEY` is configured, advice is generated through OpenAI; otherwise, the backend uses its built-in rule-based advice.

## What to say in the pitch
“Shops Like Yours turns merchant payment patterns into simple, personalized actions. In this prototype, we demonstrate the workflow with synthetic data. With authorized Paytm data, privacy-preserving peer groups, and measured experiments, the product could provide trustworthy benchmarks at scale.”

## Before production
- Replace synthetic data with an approved secure data source.
- Use anonymized/aggregated peer groups and minimum cohort thresholds.
- Add authentication, authorization, input validation, rate limiting, audit logs, and secret management.
- Evaluate recommendations with randomized holdout tests; do not claim uplift without measured results.
- Review privacy, cost, and safety controls before using the optional OpenAI integration with real merchant data.
