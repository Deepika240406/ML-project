"""Comprehensive test for all app modules"""
import sys, os
results = {}

def test(name, fn):
    try:
        res = fn()
        results[name] = f"PASS{' (' + res + ')' if res else ''}"
    except Exception as e:
        results[name] = f"FAIL: {e}"
    icon = "OK" if results[name].startswith("PASS") else "XX"
    print(f"  [{icon}] {name}: {results[name]}")

print("\n--- Testing Database Connection ---")
def t_db():
    from database import DatabaseManager
    db = DatabaseManager()
    if not db.connection_available:
        return "Not connected (running in CSV mode)"
    return "Neon connected"
test("database", t_db)

print("\n--- Testing Data Loader (Neon) ---")
def t_loader():
    from data_loader import DataLoader
    dl = DataLoader()
    df = dl.load_all_data()
    assert len(df) > 0, "No rows"
    return f"{len(df)} rows from Neon"
test("data_loader", t_loader)

print("\n--- Testing ML Model ---")
def t_ml():
    from data_loader import DataLoader
    from ml_model import RealEstatePricePredictor
    df = DataLoader().load_all_data()
    ml = RealEstatePricePredictor()
    ml.train_model(df)
    result = ml.predict({'area_sqft': 1000, 'bhk': 2, 'city': 'mumbai',
                       'district': 'South Mumbai', 'sub_district': 'Colaba',
                       'property_type': 'Apartment', 'furnishing': 'Semi-Furnished'})
    assert result, "No prediction"
    # predict returns (price, label, details_dict)
    price = result[0] if isinstance(result, tuple) else result
    assert float(price) > 0, "Price is 0"
    return f"predicted=Rs{float(price):,.0f}"
test("ml_model", t_ml)

print("\n--- Testing EMI Calculator ---")
def t_emi():
    from emi_calculator import EMICalculator
    emi = EMICalculator()
    monthly = emi.calculate_emi(5000000, 8.5, 20)
    assert monthly > 0, "No EMI"
    details = emi.calculate_loan_details(5000000, 8.5, 20)
    assert details, "No details"
    return f"EMI=Rs{monthly:,.0f}"
test("emi_calculator", t_emi)

print("\n--- Testing Financial Calculator ---")
def t_fin():
    from financial_calculator import LoanEligibilityCalculator, TaxCalculator, RegistrationCostCalculator
    lec = LoanEligibilityCalculator()
    tc = TaxCalculator()
    rcc = RegistrationCostCalculator()
    return "3 calculators imported"
test("financial_calculator", t_fin)

print("\n--- Testing Property Analyzer ---")
def t_pa():
    from property_analyzer import PropertyAnalyzer
    pa = PropertyAnalyzer()
    return "imported"
test("property_analyzer", t_pa)

print("\n--- Testing Validators ---")
def t_val():
    from validators import DataValidator
    v = DataValidator()
    return "imported"
test("validators", t_val)

print("\n--- Testing Content System ---")
def t_cs():
    from content_system import PropertyBuyingGuide, LegalDocumentation, MarketReports, InvestmentTips
    pbg = PropertyBuyingGuide()
    ld = LegalDocumentation()
    mr = MarketReports()
    it = InvestmentTips()
    return "4 classes imported and instantiated"
test("content_system", t_cs)

print("\n--- Testing Production Config ---")
def t_cfg():
    from production_config import ProductionConfig
    cfg = ProductionConfig()
    return "instantiated"
test("production_config", t_cfg)

print("\n--- Testing Production Security ---")
def t_sec():
    from production_security import SecurityManager
    sm = SecurityManager()
    return "instantiated"
test("production_security", t_sec)

print("\n--- Testing Production Logging ---")
def t_log():
    from production_logging import ProductionLogger, get_logger
    logger = get_logger("test")
    assert logger, "No logger"
    return "logger ready"
test("production_logging", t_log)

# Summary
passed = sum(1 for v in results.values() if v.startswith("PASS"))
failed = [(k, v) for k, v in results.items() if not v.startswith("PASS")]
print(f"\n{'='*45}")
print(f"  RESULTS: {passed}/{len(results)} passed")
if failed:
    print("\n  FAILURES:")
    for k, v in failed:
        print(f"    - {k}: {v}")
print(f"{'='*45}\n")

if __name__ == '__main__':
    if failed:
        sys.exit(1)
