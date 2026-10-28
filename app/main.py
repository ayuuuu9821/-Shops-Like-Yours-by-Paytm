from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pathlib import Path
from dotenv import load_dotenv
import json
import os
import pandas as pd
import numpy as np
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "demo_sales.csv"
load_dotenv(ROOT.parent / ".env")

app = FastAPI(
    title="Shops Like Yours API",
    description="Hackathon demo: merchant sales insights, peer benchmarks, and business-growth suggestions.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this to your frontend origin before production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AdviceRequest(BaseModel):
    shop_name: str = "My Shop"
    category: str = "Kirana"
    area: str = "Sector 14"
    daily_sales: float = Field(default=18000, ge=0)
    average_bill: float = Field(default=180, ge=0)
    language: str = "English"
    period: str = "weekly"

def sales_data():
    if not DATA_PATH.exists():
        raise HTTPException(status_code=500, detail="Demo sales data file is missing.")
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])
    return df

def generate_ai_advice(req: AdviceRequest, peer_avg: float, low: bool):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    payload = {
        "model": model,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "Give a practical, low-risk business experiment for a small shop. "
                    "Do not promise results or recommend unlawful or regulated activity. "
                    "Reply only as JSON with string fields personalized_action, "
                    "advertising_idea, and measurement. Write all fields in the requested language."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "category": req.category,
                        "daily_sales": req.daily_sales,
                        "average_bill": req.average_bill,
                        "language": req.language,
                        "period": req.period,
                        "demo_peer_average": round(peer_avg, 2),
                        "below_demo_peer_average": low,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    }
    request = Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI API returned HTTP {exc.code}. Check your API key, model access, and account limits.",
        ) from exc
    except (URLError, TimeoutError) as exc:
        raise HTTPException(status_code=502, detail="Could not connect to the OpenAI API.") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=502, detail="OpenAI API returned an invalid response.") from exc

    try:
        content = result["choices"][0]["message"]["content"]
        advice_result = json.loads(content)
        fields = ("personalized_action", "advertising_idea", "measurement")
        if not isinstance(advice_result, dict) or any(
            not isinstance(advice_result.get(field), str) or not advice_result[field].strip()
            for field in fields
        ):
            raise ValueError("Missing or invalid advice fields")
    except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="OpenAI API returned advice in an unexpected format.") from exc

    return advice_result

@app.get("/")
def root():
    return {"message": "Shops Like Yours API is running", "docs": "/docs"}

@app.get("/api/overview")
def overview(category: str = "Kirana", area: str = "Sector 14"):
    df = sales_data()
    selected = df[(df.category.str.lower() == category.lower()) & (df.area.str.lower() == area.lower())]
    if selected.empty:
        selected = df[df.category.str.lower() == category.lower()]
    if selected.empty:
        selected = df
    daily = selected.groupby("date", as_index=False).sales.sum().sort_values("date")
    total = float(daily.sales.sum())
    avg = float(daily.sales.mean()) if len(daily) else 0
    previous = float(daily.sales.iloc[:-1].mean()) if len(daily) > 1 else avg
    change = ((avg - previous) / previous * 100) if previous else 0
    return {
        "category": category,
        "area": area,
        "period": "Last 30 demo days",
        "total_sales": round(total, 2),
        "average_daily_sales": round(avg, 2),
        "sales_change_pct": round(change, 1),
        "transactions": int(selected.transactions.sum()),
        "daily_sales": [{"date": r.date.strftime("%Y-%m-%d"), "sales": round(float(r.sales), 2)}
                        for r in daily.itertuples()],
        "notice": "Illustrative synthetic data for demo only; not real Paytm merchant data."
    }

@app.get("/api/benchmark")
def benchmark(category: str = "Kirana", area: str = "Sector 14", merchant_daily_sales: float = 18000):
    df = sales_data()
    peers = df[(df.category.str.lower() == category.lower()) & (df.area.str.lower() == area.lower())]
    if peers.empty:
        peers = df[df.category.str.lower() == category.lower()]
    if peers.empty:
        peers = df
    merchant_daily_sales = max(0, float(merchant_daily_sales))
    peer_avg = float(peers.groupby("merchant_id").sales.mean().mean())
    peer_median = float(peers.groupby("merchant_id").sales.mean().median())
    if merchant_daily_sales >= peer_avg * 1.1:
        position = "Above similar shops"
        gap = merchant_daily_sales - peer_avg
    elif merchant_daily_sales >= peer_avg * 0.9:
        position = "Around the peer average"
        gap = merchant_daily_sales - peer_avg
    else:
        position = "Below similar shops"
        gap = merchant_daily_sales - peer_avg
    return {
        "category": category, "area": area,
        "merchant_daily_sales": round(merchant_daily_sales, 2),
        "peer_average_daily_sales": round(peer_avg, 2),
        "peer_median_daily_sales": round(peer_median, 2),
        "gap_vs_peer_average": round(gap, 2),
        "position": position,
        "peer_count": int(peers.merchant_id.nunique()),
        "notice": "Demo benchmark uses synthetic data, not live competitor or Paytm data."
    }

@app.post("/api/advice")
def advice(req: AdviceRequest):
    df = sales_data()
    peers = df[(df.category.str.lower() == req.category.lower()) & (df.area.str.lower() == req.area.lower())]
    peer_avg = float(peers.groupby("merchant_id").sales.mean().mean()) if not peers.empty else float(df.sales.mean())
    low = req.daily_sales < peer_avg * 0.9
    ai_advice = generate_ai_advice(req, peer_avg, low)
    if ai_advice:
        return {
            "shop_name": req.shop_name,
            "entered_daily_sales": req.daily_sales,
            "demo_peer_average": round(peer_avg, 2),
            "position": "Below demo peer average" if low else "Near/above demo peer average",
            **ai_advice,
            "caution": "AI-generated suggestions are hypotheses to test, not guaranteed results. Benchmarks use synthetic demo data.",
        }

    if req.category.lower() == "tea stall":
        action = "Test a small evening chai + snack combo for 7 days and record combo sales separately."
        campaign = "Run a 5–7 PM chai-and-snack offer; display the price clearly at the counter."
    elif req.category.lower() == "salon":
        action = "Try a weekday off-peak appointment offer for 7 days; compare bookings with the previous week."
        campaign = "Promote a limited weekday grooming package through a local WhatsApp status."
    elif req.category.lower() == "pharmacy":
        action = "Track frequently requested out-of-stock items for one week and improve availability where appropriate."
        campaign = "Share a service-focused reminder about store hours and prescription refill availability; follow applicable rules."
    else:
        action = "Test one clearly priced evening essentials bundle for 7 days and track its sales separately."
        campaign = "Promote a small essentials combo during your slowest 2-hour window; compare transactions before and after."
    if not low:
        action = "Your entered sales are near or above the demo peer benchmark. Test one small offer and measure whether it adds incremental sales without reducing margin."
    if req.language.lower().startswith("hi"):
        action = "7 din ke liye ek chhota, clearly-priced offer test karein aur uski sales alag se record karein. Phir pichhle hafte se compare karein."
        campaign = "Apne slowest 2-hour window mein ek simple offer promote karein aur transactions compare karein."
    return {
        "shop_name": req.shop_name,
        "entered_daily_sales": req.daily_sales,
        "demo_peer_average": round(peer_avg, 2),
        "position": "Below demo peer average" if low else "Near/above demo peer average",
        "personalized_action": action,
        "advertising_idea": campaign,
        "measurement": "Track daily transactions, average bill value, and gross margin for 7 days. Compare with the previous 7 days.",
        "caution": "This is a rule-based demo, not a trained generative AI model. Suggestions are hypotheses to test, not guaranteed results."
    }

@app.get("/api/categories")
def categories():
    df = sales_data()
    return {"categories": sorted(df.category.unique().tolist()),
            "areas": sorted(df.area.unique().tolist())}
