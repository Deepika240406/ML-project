import React, { useState, useEffect } from 'react';
import { 
  Building2, 
  MapPin, 
  Search, 
  Calculator, 
  TrendingUp, 
  ShieldCheck, 
  IndianRupee, 
  Sparkles, 
  ChevronRight, 
  CheckCircle2, 
  ArrowUpRight, 
  FileText, 
  Landmark, 
  Send,
  Home,
  Sliders,
  Award
} from 'lucide-react';

interface ValuationResult {
  predicted_price: number;
  price_formatted: string;
  price_per_sqft: number;
  price_per_sqft_formatted: string;
  confidence_score: number;
  investment_advice: string;
  model_breakdown: {
    ensemble: { price: number; formatted: string };
    xgboost: { price: number; formatted: string };
    random_forest: { price: number; formatted: string };
    decision_tree: { price: number; formatted: string };
  };
  rental_and_roi: {
    estimated_monthly_rent_formatted: string;
    gross_rental_yield: number;
    payback_years: number;
    indicative_emi_formatted: string;
  };
  appreciation: {
    in_5_years_formatted: string;
    in_10_years_formatted: string;
    projected_annual_growth: number;
  };
}

interface PropertyListing {
  id: string;
  title: string;
  locality: string;
  bhk: number;
  baths: number;
  area_sqft: number;
  price_formatted: string;
  price_per_sqft: string;
  status: string;
  rera: string;
  image: string;
  tags: string[];
}

export default function App() {
  const [selectedCity, setSelectedCity] = useState('Mumbai');
  const [activeTab, setActiveTab] = useState<'valuation' | 'emi' | 'stamp' | 'ai'>('valuation');
  
  // Valuation inputs
  const [district, setDistrict] = useState('Western Suburbs');
  const [subDistrict, setSubDistrict] = useState('Bandra West');
  const [areaSqft, setAreaSqft] = useState(1200);
  const [bhk, setBhk] = useState(3);
  const [propertyType, setPropertyType] = useState('Apartment');
  const [furnishing, setFurnishing] = useState('Semi-Furnished');

  // Localities dictionary
  const [districtsList, setDistrictsList] = useState<string[]>(['Western Suburbs', 'South Mumbai', 'Central Mumbai', 'Eastern Suburbs']);
  const [subDistrictsMap, setSubDistrictsMap] = useState<Record<string, string[]>>({
    'Western Suburbs': ['Bandra West', 'Andheri West', 'Juhu', 'Goregaon West', 'Versova'],
    'South Mumbai': ['Colaba', 'Nariman Point', 'Worli', 'Malabar Hill'],
    'Central Mumbai': ['Dadar East', 'Parel', 'Lower Parel'],
    'Eastern Suburbs': ['Powai', 'Ghatkopar East', 'Mulund East']
  });

  // State for valuation results
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ValuationResult | null>(null);
  const [properties, setProperties] = useState<PropertyListing[]>([]);

  // EMI calculator state
  const [emiPrice, setEmiPrice] = useState(15000000);
  const [downPaymentPct, setDownPaymentPct] = useState(20);
  const [interestRate, setInterestRate] = useState(8.5);
  const [tenureYears, setTenureYears] = useState(20);
  const [monthlyEmi, setMonthlyEmi] = useState(104140);
  const [totalInterest, setTotalInterest] = useState(12993500);

  // Stamp Duty state
  const [stampDutyPrice, setStampDutyPrice] = useState(15000000);
  const [stampGender, setStampGender] = useState('male');
  const [stampDutyAmount, setStampDutyAmount] = useState(750000);
  const [regFee, setRegFee] = useState(30000);

  // Chat state
  const [chatMessages, setChatMessages] = useState<{ role: 'user' | 'assistant'; text: string }[]>([
    { role: 'assistant', text: 'Hello! I am your 99acres AI Real Estate Advisor. Ask me anything about property valuations, RERA compliance, home loan tax deductions, or locality trends.' }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // Load localities on city change
  useEffect(() => {
    fetch(`/api/localities?city=${encodeURIComponent(selectedCity)}`)
      .then(res => res.json())
      .then(data => {
        if (data.districts && data.districts.length > 0) {
          setDistrictsList(data.districts);
          setSubDistrictsMap(data.sub_districts || {});
          setDistrict(data.districts[0]);
          const subs = (data.sub_districts && data.sub_districts[data.districts[0]]) || [];
          if (subs.length > 0) setSubDistrict(subs[0]);
        }
      })
      .catch(() => {
        // Fallback cities mapping
        const defaults: Record<string, { d: string[]; s: Record<string, string[]> }> = {
          'Mumbai': { d: ['Western Suburbs', 'South Mumbai'], s: { 'Western Suburbs': ['Bandra West', 'Andheri West'], 'South Mumbai': ['Colaba', 'Worli'] } },
          'Bangalore': { d: ['Bangalore Urban'], s: { 'Bangalore Urban': ['Whitefield', 'Electronic City', 'Koramangala', 'Indiranagar'] } },
          'Delhi': { d: ['Central Delhi', 'South Delhi'], s: { 'Central Delhi': ['Connaught Place', 'Karol Bagh'], 'South Delhi': ['Greater Kailash', 'Saket'] } },
          'Gurugram': { d: ['Gurugram'], s: { 'Gurugram': ['DLF Phase 1', 'DLF Phase 2', 'Golf Course Road'] } },
          'Noida': { d: ['Noida'], s: { 'Noida': ['Sector 1', 'Sector 43', 'Sector 62'] } }
        };
        const def = defaults[selectedCity] || defaults['Mumbai'];
        setDistrictsList(def.d);
        setSubDistrictsMap(def.s);
        setDistrict(def.d[0]);
        setSubDistrict(def.s[def.d[0]][0]);
      });

    // Load featured properties for selected city
    fetch(`/api/featured-properties?city=${encodeURIComponent(selectedCity)}`)
      .then(res => res.json())
      .then(data => {
        if (data.properties) setProperties(data.properties);
      })
      .catch(() => {});
  }, [selectedCity]);

  // Handle District change to update subDistrict
  const handleDistrictChange = (d: string) => {
    setDistrict(d);
    const subs = subDistrictsMap[d] || [];
    if (subs.length > 0) setSubDistrict(subs[0]);
  };

  // Perform Property Price Prediction
  const handlePredict = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          city: selectedCity,
          district: district || selectedCity,
          sub_district: subDistrict || district || selectedCity,
          area_sqft: Number(areaSqft),
          bhk: Number(bhk),
          property_type: propertyType,
          furnishing: furnishing
        })
      });
      const data = await response.json();
      if (data.success) {
        setResult(data);
        setEmiPrice(data.predicted_price);
        setStampDutyPrice(data.predicted_price);
      }
    } catch (err) {
      console.error('Prediction error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Run calculation on initial load
  useEffect(() => {
    handlePredict();
  }, []);

  // Calculate EMI
  useEffect(() => {
    const loan = emiPrice * (1 - downPaymentPct / 100);
    const r = (interestRate / 12) / 100;
    const n = tenureYears * 12;
    if (r > 0 && n > 0 && loan > 0) {
      const emi = (loan * r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1);
      setMonthlyEmi(Math.round(emi));
      setTotalInterest(Math.round((emi * n) - loan));
    }
  }, [emiPrice, downPaymentPct, interestRate, tenureYears]);

  // Calculate Stamp Duty
  useEffect(() => {
    const rates: Record<string, number> = {
      'Mumbai': stampGender === 'female' ? 0.04 : 0.05,
      'Delhi': stampGender === 'female' ? 0.04 : 0.06,
      'Bangalore': 0.05,
      'Gurugram': stampGender === 'female' ? 0.05 : 0.07,
      'Noida': stampGender === 'female' ? 0.06 : 0.07,
    };
    const rate = rates[selectedCity] || 0.05;
    const duty = Math.round(stampDutyPrice * rate);
    const reg = selectedCity === 'Mumbai' ? 30000 : Math.round(stampDutyPrice * 0.01);
    setStampDutyAmount(duty);
    setRegFee(reg);
  }, [stampDutyPrice, stampGender, selectedCity]);

  // Send AI Chat Query
  const handleSendChat = async () => {
    if (!chatInput.trim()) return;
    const q = chatInput.trim();
    setChatMessages(prev => [...prev, { role: 'user', text: q }]);
    setChatInput('');
    setChatLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, context: { city: selectedCity, locality: subDistrict } })
      });
      const data = await res.json();
      setChatMessages(prev => [...prev, { role: 'assistant', text: data.reply || 'Analysis completed.' }]);
    } catch {
      setChatMessages(prev => [...prev, { role: 'assistant', text: 'Thank you for your question. For properties in Indian metros, verify 30-year title deeds and RERA registration numbers before transaction.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* 99acres Top Navigation Bar */}
      <nav className="navbar-container">
        <div className="navbar-inner">
          <div className="flex items-center gap-6">
            <a href="#" className="brand-badge">
              <span className="logo-99">99</span>
              <div>
                <span className="logo-text">acres</span>
                <span className="logo-sub">AI Valuation Pro</span>
              </div>
            </a>

            {/* City Selector */}
            <div className="city-pill-btn">
              <MapPin size={15} className="text-amber-400" />
              <select 
                value={selectedCity} 
                onChange={(e) => setSelectedCity(e.target.value)}
                style={{ background: 'transparent', color: '#fff', border: 'none', fontWeight: 700, outline: 'none', cursor: 'pointer' }}
              >
                <option value="Mumbai" style={{ color: '#000' }}>Mumbai</option>
                <option value="Delhi" style={{ color: '#000' }}>Delhi</option>
                <option value="Bangalore" style={{ color: '#000' }}>Bangalore</option>
                <option value="Gurugram" style={{ color: '#000' }}>Gurugram</option>
                <option value="Noida" style={{ color: '#000' }}>Noida</option>
              </select>
            </div>
          </div>

          <div className="nav-links">
            <div 
              className={`nav-item ${activeTab === 'valuation' ? 'active' : ''}`}
              onClick={() => setActiveTab('valuation')}
            >
              <Calculator size={16} /> Property Valuation
            </div>
            <div 
              className={`nav-item ${activeTab === 'emi' ? 'active' : ''}`}
              onClick={() => setActiveTab('emi')}
            >
              <IndianRupee size={16} /> EMI & Loan
            </div>
            <div 
              className={`nav-item ${activeTab === 'stamp' ? 'active' : ''}`}
              onClick={() => setActiveTab('stamp')}
            >
              <Landmark size={16} /> Stamp Duty
            </div>
            <div 
              className={`nav-item ${activeTab === 'ai' ? 'active' : ''}`}
              onClick={() => setActiveTab('ai')}
            >
              <Sparkles size={16} className="text-amber-400" /> 99AI Advisor
            </div>
            <button className="btn-post-property">
              Post Property <span className="bg-white/20 text-xs px-1.5 py-0.5 rounded uppercase">FREE</span>
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section Banner */}
      <section className="hero-wrapper">
        <h1 className="hero-title">
          Real Estate Property Prices & AI Valuation in {selectedCity}
        </h1>
        <p className="hero-subtitle">
          India's #1 Predictive Valuation Engine • Multi-Model Machine Learning (XGBoost, Random Forest & Decision Trees) across 525+ Verified Registrations
        </p>
      </section>

      {/* 99acres Search & Valuation Console */}
      <div className="valuation-console-card">
        <div className="console-tabs">
          <div 
            className={`console-tab ${activeTab === 'valuation' ? 'active' : ''}`}
            onClick={() => setActiveTab('valuation')}
          >
            <Building2 size={18} /> Property Price Predictor
          </div>
          <div 
            className={`console-tab ${activeTab === 'emi' ? 'active' : ''}`}
            onClick={() => setActiveTab('emi')}
          >
            <Calculator size={18} /> Home Loan & EMI
          </div>
          <div 
            className={`console-tab ${activeTab === 'stamp' ? 'active' : ''}`}
            onClick={() => setActiveTab('stamp')}
          >
            <FileText size={18} /> Registration & Taxes
          </div>
          <div 
            className={`console-tab ${activeTab === 'ai' ? 'active' : ''}`}
            onClick={() => setActiveTab('ai')}
          >
            <Sparkles size={18} /> 99AI Investment Insights
          </div>
        </div>

        <div className="console-body">
          {activeTab === 'valuation' && (
            <div>
              <div className="form-grid">
                {/* District */}
                <div className="input-group">
                  <label className="input-label">District / Zone</label>
                  <select 
                    className="input-select"
                    value={district}
                    onChange={(e) => handleDistrictChange(e.target.value)}
                  >
                    {districtsList.map(d => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                  </select>
                </div>

                {/* Sub-District / Locality */}
                <div className="input-group">
                  <label className="input-label">Locality / Micro-Market</label>
                  <select 
                    className="input-select"
                    value={subDistrict}
                    onChange={(e) => setSubDistrict(e.target.value)}
                  >
                    {(subDistrictsMap[district] || [subDistrict]).map(s => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>

                {/* Property Type */}
                <div className="input-group">
                  <label className="input-label">Property Type</label>
                  <select 
                    className="input-select"
                    value={propertyType}
                    onChange={(e) => setPropertyType(e.target.value)}
                  >
                    <option value="Apartment">Apartment</option>
                    <option value="Villa">Villa / Independent House</option>
                    <option value="Studio">Studio Apartment</option>
                  </select>
                </div>

                {/* Furnishing */}
                <div className="input-group">
                  <label className="input-label">Furnishing Status</label>
                  <select 
                    className="input-select"
                    value={furnishing}
                    onChange={(e) => setFurnishing(e.target.value)}
                  >
                    <option value="Semi-Furnished">Semi-Furnished</option>
                    <option value="Fully Furnished">Fully Furnished</option>
                    <option value="Unfurnished">Unfurnished</option>
                  </select>
                </div>
              </div>

              {/* BHK Pills & Area Row */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
                <div>
                  <label className="input-label">Select BHK Configuration</label>
                  <div className="bhk-pill-group">
                    {[1, 2, 3, 4, 5].map(b => (
                      <div 
                        key={b}
                        className={`bhk-pill ${bhk === b ? 'active' : ''}`}
                        onClick={() => setBhk(b)}
                      >
                        {b} BHK
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <label className="input-label">Super Built-up Area (Sq.Ft)</label>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#0066cc' }}>{areaSqft} sq.ft</span>
                  </div>
                  <input 
                    type="number"
                    className="input-text"
                    style={{ width: '100%', marginTop: '4px' }}
                    value={areaSqft}
                    onChange={(e) => setAreaSqft(Math.max(100, Number(e.target.value)))}
                  />
                  <div className="area-presets">
                    {[650, 850, 1000, 1200, 1500, 2000].map(val => (
                      <span 
                        key={val} 
                        className="preset-chip"
                        onClick={() => setAreaSqft(val)}
                      >
                        {val} sqft
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <button 
                className="btn-check-price"
                onClick={handlePredict}
                disabled={loading}
              >
                {loading ? 'Evaluating Model Consensus...' : `Check Instant Estimated Price for ${subDistrict} 🔍`}
              </button>
            </div>
          )}

          {activeTab === 'emi' && (
            <div>
              <div className="form-grid">
                <div className="input-group">
                  <label className="input-label">Property Cost (₹)</label>
                  <input 
                    type="number" 
                    className="input-text" 
                    value={emiPrice} 
                    onChange={(e) => setEmiPrice(Number(e.target.value))} 
                  />
                </div>
                <div className="input-group">
                  <label className="input-label">Down Payment ({downPaymentPct}%)</label>
                  <input 
                    type="range" 
                    min="10" 
                    max="50" 
                    step="5" 
                    value={downPaymentPct} 
                    onChange={(e) => setDownPaymentPct(Number(e.target.value))} 
                  />
                  <span style={{ fontSize: '0.85rem', color: '#64748b' }}>₹{((emiPrice * downPaymentPct) / 100).toLocaleString('en-IN')}</span>
                </div>
                <div className="input-group">
                  <label className="input-label">Interest Rate ({interestRate}% p.a.)</label>
                  <input 
                    type="range" 
                    min="7.5" 
                    max="12.0" 
                    step="0.25" 
                    value={interestRate} 
                    onChange={(e) => setInterestRate(Number(e.target.value))} 
                  />
                </div>
                <div className="input-group">
                  <label className="input-label">Loan Tenure ({tenureYears} Years)</label>
                  <select 
                    className="input-select" 
                    value={tenureYears} 
                    onChange={(e) => setTenureYears(Number(e.target.value))}
                  >
                    {[10, 15, 20, 25, 30].map(y => (
                      <option key={y} value={y}>{y} Years</option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={{ background: '#f8fafc', padding: '24px', borderRadius: '12px', border: '1px solid #e2e8f0', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                <div>
                  <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 700 }}>ESTIMATED MONTHLY EMI</div>
                  <div style={{ fontSize: '2rem', fontWeight: 800, color: '#002244' }}>₹{monthlyEmi.toLocaleString('en-IN')}</div>
                  <div style={{ fontSize: '0.8rem', color: '#00875a' }}>Best Bank Offer @ {interestRate}%</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 700 }}>PRINCIPAL LOAN AMOUNT</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#0f172a' }}>₹{(emiPrice * (1 - downPaymentPct/100)).toLocaleString('en-IN')}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 700 }}>TOTAL INTEREST PAYABLE</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#d97706' }}>₹{totalInterest.toLocaleString('en-IN')}</div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'stamp' && (
            <div>
              <div className="form-grid">
                <div className="input-group">
                  <label className="input-label">Registered Property Price (₹)</label>
                  <input 
                    type="number" 
                    className="input-text" 
                    value={stampDutyPrice} 
                    onChange={(e) => setStampDutyPrice(Number(e.target.value))} 
                  />
                </div>
                <div className="input-group">
                  <label className="input-label">State Jurisdiction</label>
                  <input type="text" className="input-text" disabled value={selectedCity} />
                </div>
                <div className="input-group">
                  <label className="input-label">Buyer Gender (Concessions Applied)</label>
                  <select 
                    className="input-select" 
                    value={stampGender} 
                    onChange={(e) => setStampGender(e.target.value)}
                  >
                    <option value="male">Male (Standard Rate)</option>
                    <option value="female">Female (1% Concession in Delhi/UP)</option>
                    <option value="joint">Joint (Male + Female)</option>
                  </select>
                </div>
              </div>

              <div style={{ background: '#f0fdf4', padding: '24px', borderRadius: '12px', border: '1px solid #bbf7d0', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                <div>
                  <div style={{ fontSize: '0.8rem', color: '#166534', fontWeight: 700 }}>STAMP DUTY CHARGES</div>
                  <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#166534' }}>₹{stampDutyAmount.toLocaleString('en-IN')}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.8rem', color: '#166534', fontWeight: 700 }}>REGISTRATION CHARGES</div>
                  <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#166534' }}>₹{regFee.toLocaleString('en-IN')}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.8rem', color: '#166534', fontWeight: 700 }}>TOTAL GOVT. OUTFLOW</div>
                  <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#092244' }}>₹{(stampDutyAmount + regFee).toLocaleString('en-IN')}</div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'ai' && (
            <div className="chat-drawer">
              <div style={{ maxHeight: '280px', overflowY: 'auto', marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {chatMessages.map((msg, i) => (
                  <div 
                    key={i} 
                    style={{ 
                      alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                      backgroundColor: msg.role === 'user' ? '#0066cc' : '#f1f5f9',
                      color: msg.role === 'user' ? '#ffffff' : '#0f172a',
                      padding: '12px 18px',
                      borderRadius: '12px',
                      maxWidth: '85%',
                      fontSize: '0.92rem'
                    }}
                  >
                    {msg.text}
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', gap: '10px' }}>
                <input 
                  type="text" 
                  className="input-text" 
                  placeholder="Ask about price trends, RERA verification, legal documents in India..." 
                  style={{ flex: 1 }}
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendChat()}
                />
                <button 
                  onClick={handleSendChat}
                  disabled={chatLoading}
                  style={{ background: '#002244', color: '#fff', border: 'none', padding: '0 20px', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700 }}
                >
                  <Send size={16} /> Ask AI
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Valuation Output Dossier (when available) */}
      {result && (
        <section className="results-container">
          <div className="valuation-hero-card">
            <div className="valuation-header-row">
              <div>
                <span className="verified-pill">
                  <CheckCircle2 size={16} /> 99acres AI Verified Valuation • {result.confidence_score}% Model Consensus
                </span>
                <div style={{ marginTop: '12px' }}>
                  <div className="valuation-price-lg">{result.price_formatted}</div>
                  <div className="unit-rate-badge">
                    Estimated at <strong style={{ color: '#091e42' }}>{result.price_per_sqft_formatted}</strong> for {bhk} BHK in {subDistrict}, {selectedCity}
                  </div>
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{ background: '#f8fafc', padding: '16px 20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 700 }}>INVESTMENT VIABILITY</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#00875a' }}>⭐ {result.investment_advice}</div>
                  <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '4px' }}>Gross Yield: {result.rental_and_roi.gross_rental_yield}% p.a.</div>
                </div>
              </div>
            </div>

            {/* 4-Model Ensemble Consensus Comparison */}
            <div>
              <div style={{ fontSize: '0.9rem', fontWeight: 800, color: '#334155', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                🤖 Multi-Model Ensemble Intelligence Breakdown
              </div>
              <div className="models-grid">
                <div className="model-card featured">
                  <div className="model-name" style={{ color: '#0066cc' }}>🏆 Ensemble Model (Consensus)</div>
                  <div className="model-val">{result.model_breakdown.ensemble.formatted}</div>
                  <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '4px' }}>Weighted aggregate of 3 architectures</div>
                </div>

                <div className="model-card">
                  <div className="model-name">⚡ XGBoost Regressor</div>
                  <div className="model-val">{result.model_breakdown.xgboost.formatted}</div>
                  <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '4px' }}>Gradient boosted decision trees</div>
                </div>

                <div className="model-card">
                  <div className="model-name">🌲 Random Forest</div>
                  <div className="model-val">{result.model_breakdown.random_forest.formatted}</div>
                  <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '4px' }}>100 estimators ensemble</div>
                </div>

                <div className="model-card">
                  <div className="model-name">🌿 Decision Tree</div>
                  <div className="model-val">{result.model_breakdown.decision_tree.formatted}</div>
                  <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '4px' }}>Tree-based regression splits</div>
                </div>
              </div>
            </div>

            {/* Financial & ROI Quick Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginTop: '20px' }}>
              <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 700 }}>INDICATIVE MONTHLY EMI</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#002244' }}>{result.rental_and_roi.indicative_emi_formatted}</div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Assumes 80% loan @ 8.5% for 20 years</div>
              </div>

              <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 700 }}>5-YEAR PROJECTED VALUATION</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#00875a' }}>{result.appreciation.in_5_years_formatted}</div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Projected at +{result.appreciation.projected_annual_growth}% YoY growth</div>
              </div>

              <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 700 }}>RENTAL EARNING ESTIMATE</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#d97706' }}>{result.rental_and_roi.estimated_monthly_rent_formatted}</div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Payback Horizon: ~{result.rental_and_roi.payback_years} years</div>
              </div>
            </div>
          </div>

          {/* 99acres Featured Verified Listings in Locality */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#002244' }}>
                  Verified Properties in {selectedCity}
                </h2>
                <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
                  Top RERA-registered developments with verified documents and seller credentials
                </p>
              </div>
              <button 
                onClick={() => alert(`Showing all available listings for ${selectedCity}`)}
                style={{ background: 'transparent', color: '#0066cc', fontWeight: 700, border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
              >
                View all in {selectedCity} <ChevronRight size={16} />
              </button>
            </div>

            <div className="property-cards-grid">
              {properties.map(p => (
                <div key={p.id} className="property-card">
                  <img src={p.image} alt={p.title} className="property-img" />
                  <div className="property-body">
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '8px' }}>
                      {p.tags.map(t => (
                        <span key={t} style={{ fontSize: '0.72rem', fontWeight: 700, padding: '2px 8px', borderRadius: '4px', backgroundColor: '#e8f1fd', color: '#0066cc' }}>
                          {t}
                        </span>
                      ))}
                    </div>
                    <div className="property-title">{p.title}</div>
                    <div className="property-locality">
                      <MapPin size={13} /> {p.locality}
                    </div>

                    <div className="property-specs">
                      <span>{p.bhk} BHK</span>
                      <span>•</span>
                      <span>{p.baths} Baths</span>
                      <span>•</span>
                      <span>{p.area_sqft} sq.ft</span>
                    </div>

                    <div className="property-footer">
                      <div>
                        <div className="property-price">{p.price_formatted}</div>
                        <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{p.price_per_sqft}</div>
                      </div>
                      <button className="btn-contact">Contact Seller</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Official 99acres Footer */}
      <footer className="footer-container">
        <div style={{ maxWidth: '1280px', margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '32px', marginBottom: '32px' }}>
          <div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fff', marginBottom: '12px' }}>99acres AI Valuation</div>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
              India's comprehensive property valuation, market rate tracking, and investment intelligence portal.
            </p>
          </div>
          <div>
            <div style={{ fontWeight: 700, color: '#fff', marginBottom: '10px' }}>Top Metros</div>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <li><a href="#" style={{ color: '#94a3b8', textDecoration: 'none' }}>Mumbai Properties & Valuation</a></li>
              <li><a href="#" style={{ color: '#94a3b8', textDecoration: 'none' }}>Delhi Real Estate Rates</a></li>
              <li><a href="#" style={{ color: '#94a3b8', textDecoration: 'none' }}>Bangalore Tech Corridor Prices</a></li>
              <li><a href="#" style={{ color: '#94a3b8', textDecoration: 'none' }}>Gurugram Golf Course Extn</a></li>
              <li><a href="#" style={{ color: '#94a3b8', textDecoration: 'none' }}>Noida Expressway Projects</a></li>
            </ul>
          </div>
          <div>
            <div style={{ fontWeight: 700, color: '#fff', marginBottom: '10px' }}>Financial Tools</div>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <li><a href="#" style={{ color: '#94a3b8', textDecoration: 'none' }}>Home Loan EMI Calculator</a></li>
              <li><a href="#" style={{ color: '#94a3b8', textDecoration: 'none' }}>Stamp Duty & Registration Fee</a></li>
              <li><a href="#" style={{ color: '#94a3b8', textDecoration: 'none' }}>Bank Loan Eligibility Checker</a></li>
              <li><a href="#" style={{ color: '#94a3b8', textDecoration: 'none' }}>RERA Document Verification</a></li>
            </ul>
          </div>
        </div>
        <div style={{ textAlign: 'center', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '20px', fontSize: '0.8rem', color: '#64748b' }}>
          Disclaimer: 99acres AI Valuation provides estimated property prices based on historical transaction datasets and machine learning algorithms. All registered projects are subject to state RERA guidelines.
        </div>
      </footer>
    </div>
  );
}
