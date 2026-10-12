"""
FastAPI Backend for 99acres-Style Real Estate AI Platform
Provides high-performance REST APIs for property valuation, ML ensemble models,
financial tools, stamp duty calculations, and AI assistant.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import os
import sys
from pathlib import Path
import math

# Ensure app directory is in python path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from data_loader import DataLoader
from ml_model import RealEstatePricePredictor
from emi_calculator import EMICalculator
from financial_calculator import LoanEligibilityCalculator, RegistrationCostCalculator
from gemini_ai import GeminiAIService

app = FastAPI(
    title="99Valuation AI Engine",
    description="Institutional Real Estate Valuation and Advisory API for Indian Metros",
    version="2.0.0"
)

# Enable CORS for React frontend (Vite port 5173 / 3000 / localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances initialized on startup
data_loader = None
predictor = None
emi_calc = None
loan_calc = None
reg_calc = None
gemini_service = None
combined_data = None

@app.on_event("startup")
def startup_event():
    global data_loader, predictor, emi_calc, loan_calc, reg_calc, gemini_service, combined_data
    print("[INIT] Initializing 99acres-Style AI Valuation Engine...")
    data_loader = DataLoader()
    combined_data = data_loader.load_all_data()
    
    predictor = RealEstatePricePredictor()
    if combined_data is not None and not combined_data.empty:
        predictor.train_model(combined_data)
        print(f"[OK] ML Ensemble Models Trained on {len(combined_data)} properties.")
    else:
        print("[WARN] Data loader returned empty DataFrame.")

    emi_calc = EMICalculator()
    loan_calc = LoanEligibilityCalculator()
    reg_calc = RegistrationCostCalculator()
    gemini_service = GeminiAIService()
    print("[READY] API Startup Complete. Server ready.")

# --- Data Schemas ---
class PredictionRequest(BaseModel):
    city: str = Field(..., example="Mumbai")
    district: str = Field(..., example="Western Suburbs")
    sub_district: str = Field(..., example="Bandra West")
    area_sqft: float = Field(..., example=1200)
    bhk: int = Field(..., example=3)
    property_type: str = Field(..., example="Apartment")
    furnishing: str = Field(default="Semi-Furnished", example="Semi-Furnished")

class EMIRequest(BaseModel):
    property_price: float = Field(..., example=15000000)
    down_payment_percent: float = Field(default=20, example=20)
    interest_rate: float = Field(default=8.5, example=8.5)
    tenure_years: int = Field(default=20, example=20)

class StampDutyRequest(BaseModel):
    city: str = Field(..., example="Mumbai")
    property_price: float = Field(..., example=15000000)
    gender: str = Field(default="male", example="male")

class LoanEligibilityRequest(BaseModel):
    monthly_income: float = Field(..., example=150000)
    existing_emi: float = Field(default=0, example=20000)
    tenure_years: int = Field(default=20, example=20)
    interest_rate: float = Field(default=8.5, example=8.5)

class ChatRequest(BaseModel):
    question: str = Field(..., example="Is Bandra West a good investment for 3 BHK?")
    context: Optional[Dict[str, Any]] = None

def format_inr(number: float) -> str:
    """Format currency in Indian Lakhs and Crores"""
    if number >= 10000000:
        cr = number / 10000000
        return f"₹{cr:.2f} Cr"
    elif number >= 100000:
        lakh = number / 100000
        return f"₹{lakh:.2f} L"
    else:
        return f"₹{number:,.0f}"

# --- Endpoints ---

@app.get("/api/health")
def health():
    return {
        "status": "online",
        "service": "99acres-Style AI Valuation Engine",
        "total_properties": len(combined_data) if combined_data is not None else 0,
        "is_ai_cloud": getattr(gemini_service, "is_online", False)
    }

@app.get("/api/cities")
def get_cities():
    cities_meta = [
        {
            "name": "Mumbai",
            "tagline": "Financial Capital • Maximum Returns",
            "avg_sqft": "₹19,500/sq.ft",
            "growth": "+8.4% YoY",
            "image": "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?auto=format&fit=crop&w=600&q=80"
        },
        {
            "name": "Delhi",
            "tagline": "National Capital • Prime Connectivity",
            "avg_sqft": "₹14,200/sq.ft",
            "growth": "+7.1% YoY",
            "image": "https://images.unsplash.com/photo-1587474260584-136574528ed5?auto=format&fit=crop&w=600&q=80"
        },
        {
            "name": "Bangalore",
            "tagline": "Silicon Valley • Tech Corridor Boom",
            "avg_sqft": "₹9,800/sq.ft",
            "growth": "+11.2% YoY",
            "image": "https://images.unsplash.com/photo-1596176530529-78163a4f7af2?auto=format&fit=crop&w=600&q=80"
        },
        {
            "name": "Gurugram",
            "tagline": "Millennium City • Luxury High-Rises",
            "avg_sqft": "₹11,400/sq.ft",
            "growth": "+9.6% YoY",
            "image": "https://images.unsplash.com/photo-1582407947304-fd86f028f716?auto=format&fit=crop&w=600&q=80"
        },
        {
            "name": "Noida",
            "tagline": "Expressway Corridor • Airport Catalyst",
            "avg_sqft": "₹7,200/sq.ft",
            "growth": "+12.8% YoY",
            "image": "https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&w=600&q=80"
        }
    ]
    return {"cities": cities_meta}

@app.get("/api/localities")
def get_localities(city: str):
    city_clean = city.strip().title()
    if data_loader is None:
        raise HTTPException(status_code=500, detail="Data loader not initialized")
    districts = data_loader.get_districts_by_city(city_clean, combined_data)
    
    # Pre-aggregate sub-districts map
    sub_map = {}
    for d in districts:
        subs = data_loader.get_subdistricts_by_district(city_clean, d, combined_data)
        sub_map[d] = subs

    return {
        "city": city_clean,
        "districts": districts,
        "sub_districts": sub_map
    }

@app.post("/api/predict")
def predict_valuation(req: PredictionRequest):
    if predictor is None:
        raise HTTPException(status_code=500, detail="Model predictor not initialized")

    data_payload = {
        'city': req.city.strip().title(),
        'district': req.district.strip(),
        'sub_district': req.sub_district.strip(),
        'area_sqft': req.area_sqft,
        'bhk': req.bhk,
        'property_type': req.property_type,
        'furnishing': req.furnishing
    }

    try:
        predicted_price, investment_advice, model_preds = predictor.predict(data_payload)
        
        area = max(req.area_sqft, 50)
        price_val = float(predicted_price)
        price_per_sqft = price_val / area
        
        # 5-year Market Trend Forecast
        trends = predictor.predict_market_trends(req.city, years_ahead=5)
        
        # Appreciation Projections
        appr_5yr = price_val * ((1 + 0.088) ** 5)
        appr_10yr = price_val * ((1 + 0.088) ** 10)
        
        # Rental & ROI
        est_monthly_rent = max(8000, price_val * 0.0032)
        annual_rent = est_monthly_rent * 12
        gross_yield = (annual_rent / price_val) * 100
        payback_years = price_val / annual_rent if annual_rent > 0 else 25

        # Monthly EMI benchmark (80% LTV, 8.5%, 20 yrs)
        loan_amt = price_val * 0.8
        monthly_emi = emi_calc.calculate_emi(loan_amt, 8.5, 20)

        # Confidence Score based on model consensus
        preds_list = [v for v in model_preds.values() if isinstance(v, (int, float)) and v > 0]
        if preds_list and len(preds_list) > 1:
            diff = (max(preds_list) - min(preds_list)) / price_val
            confidence = max(82, min(97, int(100 - (diff * 50))))
        else:
            confidence = 94
        xgb_val = float(model_preds.get("xgboost", price_val))
        rf_val = float(model_preds.get("random_forest", price_val))
        dt_val = float(model_preds.get("decision_tree", price_val))

        clean_trends = []
        if trends and "predictions" in trends:
            for t in trends["predictions"]:
                clean_trends.append({
                    "year": int(t.get("year", 2026)),
                    "predicted_avg_price": float(t.get("predicted_avg_price", price_val)),
                    "price_per_sqft": float(t.get("price_per_sqft", price_per_sqft))
                })

        return {
            "success": True,
            "predicted_price": price_val,
            "price_formatted": format_inr(price_val),
            "price_per_sqft": int(price_per_sqft),
            "price_per_sqft_formatted": f"₹{int(price_per_sqft):,}/sq.ft",
            "confidence_score": int(confidence),
            "investment_advice": str(investment_advice),
            "model_breakdown": {
                "ensemble": {"price": price_val, "formatted": format_inr(price_val)},
                "xgboost": {"price": xgb_val, "formatted": format_inr(xgb_val)},
                "random_forest": {"price": rf_val, "formatted": format_inr(rf_val)},
                "decision_tree": {"price": dt_val, "formatted": format_inr(dt_val)},
            },
            "rental_and_roi": {
                "estimated_monthly_rent": int(est_monthly_rent),
                "estimated_monthly_rent_formatted": format_inr(est_monthly_rent) + "/mo",
                "gross_rental_yield": round(float(gross_yield), 2),
                "payback_years": round(float(payback_years), 1),
                "indicative_emi": int(monthly_emi),
                "indicative_emi_formatted": format_inr(monthly_emi) + "/mo"
            },
            "appreciation": {
                "in_5_years": int(appr_5yr),
                "in_5_years_formatted": format_inr(appr_5yr),
                "in_10_years": int(appr_10yr),
                "in_10_years_formatted": format_inr(appr_10yr),
                "projected_annual_growth": 8.8
            },
            "trends": clean_trends
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Valuation failed: {str(e)}")

@app.post("/api/calculate-emi")
def calculate_emi(req: EMIRequest):
    down_payment = req.property_price * (req.down_payment_percent / 100)
    loan_amount = max(0, req.property_price - down_payment)
    
    emi = emi_calc.calculate_emi(loan_amount, req.interest_rate, req.tenure_years)
    total_months = req.tenure_years * 12
    total_payable = emi * total_months
    total_interest = max(0, total_payable - loan_amount)

    return {
        "monthly_emi": int(emi),
        "monthly_emi_formatted": format_inr(emi) + "/mo",
        "loan_amount": int(loan_amount),
        "loan_amount_formatted": format_inr(loan_amount),
        "down_payment": int(down_payment),
        "down_payment_formatted": format_inr(down_payment),
        "total_interest": int(total_interest),
        "total_interest_formatted": format_inr(total_interest),
        "total_payable": int(total_payable),
        "total_payable_formatted": format_inr(total_payable),
        "interest_ratio_percent": round((total_interest / total_payable) * 100, 1) if total_payable > 0 else 0
    }

@app.post("/api/stamp-duty")
def calculate_stamp_duty(req: StampDutyRequest):
    state_map = {
        "Mumbai": "Maharashtra",
        "Delhi": "Delhi",
        "Bangalore": "Karnataka",
        "Gurugram": "Haryana",
        "Noida": "Uttar Pradesh"
    }
    state = state_map.get(req.city.strip().title(), "Maharashtra")
    
    # State-wise rates
    rates = {
        "Maharashtra": {"male": 0.05, "female": 0.04, "joint": 0.04, "reg": 0.01},
        "Delhi": {"male": 0.06, "female": 0.04, "joint": 0.04, "reg": 0.01},
        "Karnataka": {"male": 0.05, "female": 0.05, "joint": 0.05, "reg": 0.01},
        "Haryana": {"male": 0.07, "female": 0.05, "joint": 0.06, "reg": 0.01},
        "Uttar Pradesh": {"male": 0.07, "female": 0.06, "joint": 0.065, "reg": 0.01}
    }
    st_rates = rates.get(state, rates["Maharashtra"])
    rate = st_rates.get(req.gender.lower(), st_rates["male"])
    reg_rate = st_rates["reg"]

    stamp_duty = req.property_price * rate
    registration_fee = min(30000, req.property_price * reg_rate) if state == "Maharashtra" else (req.property_price * reg_rate)
    total_cost = stamp_duty + registration_fee

    return {
        "state": state,
        "city": req.city,
        "stamp_duty": int(stamp_duty),
        "stamp_duty_formatted": format_inr(stamp_duty),
        "stamp_duty_percent": round(rate * 100, 1),
        "registration_fee": int(registration_fee),
        "registration_fee_formatted": format_inr(registration_fee),
        "total_government_charges": int(total_cost),
        "total_government_charges_formatted": format_inr(total_cost)
    }

@app.post("/api/loan-eligibility")
def check_loan_eligibility(req: LoanEligibilityRequest):
    # Standard bank FOIR: 50%
    available_monthly_emi = max(0, (req.monthly_income * 0.50) - req.existing_emi)
    
    r = (req.interest_rate / 12) / 100
    n = req.tenure_years * 12
    if r > 0 and n > 0:
        max_loan = available_monthly_emi * ((1 + r)**n - 1) / (r * (1 + r)**n)
    else:
        max_loan = 0

    return {
        "max_eligible_loan": int(max_loan),
        "max_eligible_loan_formatted": format_inr(max_loan),
        "max_permissible_emi": int(available_monthly_emi),
        "max_permissible_emi_formatted": format_inr(available_monthly_emi) + "/mo",
        "monthly_income": req.monthly_income,
        "bank_comparisons": [
            {"bank": "State Bank of India (SBI)", "rate": 8.50, "max_loan": int(max_loan), "formatted": format_inr(max_loan)},
            {"bank": "HDFC Bank", "rate": 8.75, "max_loan": int(max_loan * 0.98), "formatted": format_inr(max_loan * 0.98)},
            {"bank": "ICICI Bank", "rate": 8.65, "max_loan": int(max_loan * 0.99), "formatted": format_inr(max_loan * 0.99)},
            {"bank": "Axis Bank", "rate": 8.80, "max_loan": int(max_loan * 0.97), "formatted": format_inr(max_loan * 0.97)}
        ]
    }

@app.post("/api/chat")
def chat_ai(req: ChatRequest):
    if gemini_service is None:
        raise HTTPException(status_code=500, detail="AI Service unavailable")
    
    response = gemini_service.real_estate_qa(req.question, req.context)
    return {
        "reply": response,
        "source": "OpenRouter LLM" if getattr(gemini_service, "is_online", False) else "99acres Expert Intelligence Engine"
    }

@app.get("/api/featured-properties")
def get_featured_properties(city: Optional[str] = "Mumbai"):
    city_name = (city or "Mumbai").strip().title()
    
    # Curated real-estate showcase formatted in 99acres style
    properties_db = {
        "Mumbai": [
            {
                "id": "mum-01",
                "title": "Lodha Park Luxury Residences",
                "locality": "Worli, South Mumbai",
                "bhk": 3,
                "baths": 3,
                "area_sqft": 1450,
                "price": 38500000,
                "price_formatted": "₹3.85 Cr",
                "price_per_sqft": "₹26,550/sq.ft",
                "status": "Ready to Move",
                "rera": "P51900001339",
                "image": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=700&q=80",
                "tags": ["RERA Approved", "Sea View", "Verified Seller"]
            },
            {
                "id": "mum-02",
                "title": "Rustomjee Seasons Grandeur",
                "locality": "Bandra East, Western Suburbs",
                "bhk": 2,
                "baths": 2,
                "area_sqft": 950,
                "price": 24500000,
                "price_formatted": "₹2.45 Cr",
                "price_per_sqft": "₹25,780/sq.ft",
                "status": "Ready to Move",
                "rera": "P51800001433",
                "image": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=700&q=80",
                "tags": ["BKC Connectivity", "Clubhouse", "Zero Brokerage"]
            },
            {
                "id": "mum-03",
                "title": "Hiranandani Gardens Heritage",
                "locality": "Powai, Eastern Suburbs",
                "bhk": 3,
                "baths": 3,
                "area_sqft": 1380,
                "price": 21500000,
                "price_formatted": "₹2.15 Cr",
                "price_per_sqft": "₹15,570/sq.ft",
                "status": "Under Construction",
                "rera": "P51800000145",
                "image": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=700&q=80",
                "tags": ["Township Living", "Lake View", "Verified"]
            }
        ],
        "Bangalore": [
            {
                "id": "blr-01",
                "title": "Prestige Shantiniketan Towers",
                "locality": "Whitefield, Bangalore East",
                "bhk": 3,
                "baths": 3,
                "area_sqft": 1580,
                "price": 14500000,
                "price_formatted": "₹1.45 Cr",
                "price_per_sqft": "₹9,170/sq.ft",
                "status": "Ready to Move",
                "rera": "PRM/KA/RERA/1251/446/PR/170915/000234",
                "image": "https://images.unsplash.com/photo-1600565193348-f74bd3c7ccdf?auto=format&fit=crop&w=700&q=80",
                "tags": ["IT Corridor", "Metro Walking", "Verified"]
            },
            {
                "id": "blr-02",
                "title": "Sobha Royal Pavilion",
                "locality": "Sarjapur Road, Bangalore",
                "bhk": 2,
                "baths": 2,
                "area_sqft": 1250,
                "price": 10500000,
                "price_formatted": "₹1.05 Cr",
                "price_per_sqft": "₹8,400/sq.ft",
                "status": "Ready to Move",
                "rera": "PRM/KA/RERA/1251/446/PR/190204/002338",
                "image": "https://images.unsplash.com/photo-1600585154526-990dced4db0d?auto=format&fit=crop&w=700&q=80",
                "tags": ["Rajasthani Architecture", "High ROI", "Zero Brokerage"]
            }
        ],
        "Delhi": [
            {
                "id": "del-01",
                "title": "DLF One Midtown",
                "locality": "Moti Nagar, West Delhi",
                "bhk": 3,
                "baths": 3,
                "area_sqft": 1600,
                "price": 31500000,
                "price_formatted": "₹3.15 Cr",
                "price_per_sqft": "₹19,680/sq.ft",
                "status": "Under Construction",
                "rera": "DLRERA2021P0007",
                "image": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=700&q=80",
                "tags": ["Green Belt", "Metro Connected", "Verified"]
            }
        ],
        "Gurugram": [
            {
                "id": "gur-01",
                "title": "DLF The Camellias Ultra-Luxury",
                "locality": "Golf Course Road, Gurugram",
                "bhk": 4,
                "baths": 4,
                "area_sqft": 2400,
                "price": 48500000,
                "price_formatted": "₹4.85 Cr",
                "price_per_sqft": "₹20,200/sq.ft",
                "status": "Ready to Move",
                "rera": "HRERA-10-2018",
                "image": "https://images.unsplash.com/photo-1613977257363-707ba9348227?auto=format&fit=crop&w=700&q=80",
                "tags": ["Golf Course View", "Ultra High-Net-Worth", "Verified"]
            }
        ],
        "Noida": [
            {
                "id": "noi-01",
                "title": "Godrej Woods Sanctuary",
                "locality": "Sector 43, Noida Expressway",
                "bhk": 3,
                "baths": 3,
                "area_sqft": 1550,
                "price": 16500000,
                "price_formatted": "₹1.65 Cr",
                "price_per_sqft": "₹10,640/sq.ft",
                "status": "Ready to Move",
                "rera": "UPRERAPRJ704730",
                "image": "https://images.unsplash.com/photo-1512915922686-57c11dde9b6b?auto=format&fit=crop&w=700&q=80",
                "tags": ["Forest Themed", "Near Noida Expressway", "Verified"]
            }
        ]
    }
    
    props = properties_db.get(city_name, properties_db["Mumbai"])
    return {"city": city_name, "properties": props}

# Mount static files if frontend build exists
dist_path = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if dist_path.exists():
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
