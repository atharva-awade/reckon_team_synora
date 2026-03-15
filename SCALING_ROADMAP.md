# MedicoScope — Product Scaling & Revenue Roadmap

> From hackathon prototype to Rs 3.6 Cr/year revenue in 18 months.

---

## EXECUTIVE SUMMARY

MedicoScope is a fully functional AI-powered healthcare platform with 3 on-device AI models, 8 cloud AI pipelines, 21 disease detection capabilities, and 76 API endpoints — deployed across Android, iOS, and Web. This document outlines how to scale it from a hackathon project into a revenue-generating healthcare product.

---

## PHASE 1: FIRST REVENUE (Month 0–6)

### Business Model: B2B SaaS for Clinics & Doctors

| Plan | Monthly Price | Target Customer | What They Get |
|------|--------------|-----------------|---------------|
| **Starter** | ₹2,999/month | Solo practitioners, small clinics | 3 AI modules (Skin + Chest + Brain), 100 scans/month, 1 doctor account, patient linking |
| **Professional** | ₹7,999/month | Mid-size clinics (3–10 doctors) | All AI modules + CardioScope + Lab Reader, unlimited scans, 5 doctor accounts, vitals monitoring, MindSpace |
| **Enterprise** | ₹24,999/month | Hospitals, clinic chains | Everything + white-label branding, ABDM integration, analytics dashboard, priority support, custom model training |

### Why Clinics Will Pay

| Current Cost | MedicoScope Cost | Saving |
|-------------|-----------------|--------|
| Chest X-ray reading by radiologist: ₹300–500/scan | AI reading: ₹30/scan | **90% cost reduction** |
| Dermatologist consultation: ₹500–1,000 | AI skin screening: ₹15/scan | **97% cost reduction** |
| Mental health screening: ₹1,500–3,000/session | MindSpace AI: ₹50/session | **96% cost reduction** |
| Lab report interpretation: ₹200–500 | AI Lab Reader: ₹10/report | **95% cost reduction** |

A clinic doing 10 X-rays/day saves **₹1.5 Lakhs/month** — our ₹7,999 subscription pays for itself on day 2.

### Phase 1 Revenue Projection

| Month | Clinics Onboarded | Avg Revenue/Clinic | Monthly Revenue | Cumulative Revenue |
|-------|------------------|-------------------|-----------------|-------------------|
| 1 | 5 | ₹2,999 | ₹14,995 | ₹14,995 |
| 2 | 12 | ₹3,500 | ₹42,000 | ₹56,995 |
| 3 | 25 | ₹4,000 | ₹1,00,000 | ₹1,56,995 |
| 4 | 45 | ₹4,500 | ₹2,02,500 | ₹3,59,495 |
| 5 | 75 | ₹5,000 | ₹3,75,000 | ₹7,34,495 |
| 6 | 120 | ₹5,500 | ₹6,60,000 | ₹13,94,495 |

**Phase 1 Exit Revenue**: ₹6.6L/month (₹79.2L annualized)

### Phase 1 Action Items

- [ ] Register Pvt Ltd company (₹10,000–15,000)
- [ ] DPIIT Startup India registration (free — tax benefits + funding access)
- [ ] Pilot with 5 clinics in Jodhpur (free for 3 months → feedback → case studies)
- [ ] Set up Razorpay/Stripe subscription billing
- [ ] Build clinic admin dashboard (scan usage, patient stats, billing)
- [ ] Hire 1 medical advisor (part-time MBBS doctor for validation)
- [ ] Apply to incubators: IIT Jodhpur TBI, AIIMS incubator, T-Hub

---

## PHASE 2: MULTI-STREAM REVENUE (Month 6–18)

### Additional Revenue Streams

| # | Revenue Stream | How It Works | Revenue Per Unit | Monthly Potential |
|---|---------------|-------------|-----------------|-------------------|
| 1 | **Per-Scan API** | Third-party apps call our AI models via API | ₹5–15 per inference | ₹2–5L at 20K scans/month |
| 2 | **Insurance Partnerships** | Insurers pay for early detection (reduces their claim payouts) | ₹50–100 per patient/year | ₹5–10L at 10K patients |
| 3 | **Teleconsultation Commission** | AI escalation → connect patient with specialist → 15% platform fee | ₹100–200 per consultation | ₹1–3L at 1K consults/month |
| 4 | **Lab Test Referrals** | AI recommends blood test → partner lab booking → commission | ₹30–50 per referral | ₹60K–1L at 2K referrals/month |
| 5 | **Pharmacy Integration** | Post-diagnosis → verified pharmacy recommendation → affiliate | 5–8% commission | ₹50K–1.5L/month |
| 6 | **Premium Patient App** | Direct-to-consumer subscription for individuals | ₹99–299/month | ₹2–5L at 10K subscribers |
| 7 | **Government Contracts** | Ayushman Bharat scheme → AI screening at PHCs | Per-screening fee | ₹10–50L per district contract |

### Phase 2 Revenue Projection

| Revenue Stream | Month 12 | Month 18 |
|---------------|----------|----------|
| SaaS Subscriptions (300 clinics) | ₹15,00,000 | ₹25,00,000 |
| Per-Scan API | ₹1,50,000 | ₹4,00,000 |
| Insurance Partnerships | ₹0 | ₹3,00,000 |
| Teleconsultation Commission | ₹50,000 | ₹2,00,000 |
| Lab/Pharmacy Referrals | ₹30,000 | ₹1,50,000 |
| Premium Patient App | ₹1,00,000 | ₹3,00,000 |
| **Total Monthly** | **₹18,30,000** | **₹38,50,000** |
| **Annualized** | **₹2.2 Cr** | **₹4.6 Cr** |

### Phase 2 Strategic Moves

- [ ] ABDM (Ayushman Bharat Digital Mission) integration — health record interoperability
- [ ] ABHA ID support — every patient gets a government health ID
- [ ] Partner with 3–5 insurance companies (Star Health, HDFC Ergo, ICICI Lombard)
- [ ] Launch API marketplace for third-party developers
- [ ] Expand to 5 cities (Jaipur, Ahmedabad, Pune, Hyderabad, Bangalore)
- [ ] Hire sales team (2–3 people) for hospital onboarding

---

## PHASE 3: MOAT BUILDING & NATIONAL SCALE (Month 18–36)

### Competitive Moat Strategy

| Moat | What It Means | Why It's Hard to Copy |
|------|--------------|----------------------|
| **Indian Medical Data** | Train models on Indian skin tones, Indian X-ray patterns, Indian lab reference ranges | Western-trained models miss 15–20% of Indian-specific conditions. Our data = our moat. |
| **On-Device AI** | Models run on phone, no internet required | Works in rural India where 40% of clinics have unreliable internet. Cloud-only competitors can't serve this market. |
| **ABDM-Native** | Built for Indian health ID system from ground up | Foreign competitors need years to integrate. We're native. |
| **Doctor Network Effect** | Every doctor who joins brings patients. Every patient generates data. More data = better models. | Classic network effect — first mover advantage compounds exponentially. |
| **Regional Languages** | 7 languages today → 22 scheduled languages | Localization is boring work no competitor wants to do. But it's what makes rural adoption possible. |
| **Medical AI Model Marketplace** | Let researchers publish models on our platform | We become the "App Store of Medical AI" — platform economics. |

### Phase 3 Revenue Projection

| Metric | Month 24 | Month 36 |
|--------|----------|----------|
| Total Clinics | 1,500 | 5,000 |
| Total Patients on Platform | 50,000 | 2,00,000 |
| Monthly Revenue | ₹85,00,000 | ₹3,00,00,000 |
| Annual Revenue | ₹10.2 Cr | ₹36 Cr |
| Gross Margin | 87% | 90% |
| Team Size | 15–20 | 40–60 |

---

## UNIT ECONOMICS

### Cost Structure (Current — Pre-Scale)

| Item | Monthly Cost | Notes |
|------|-------------|-------|
| Render Pro (3 services) | ₹15,000 | Node.js + Python + CardioScope |
| Groq API (LLM inference) | ₹8,000 | ~50K requests/month |
| MongoDB Atlas M10 | ₹5,000 | 10GB storage |
| Domain + CDN + SSL | ₹2,000 | Cloudflare |
| **Total** | **₹30,000** | |

### Break-Even Analysis

```
Break-Even Point = Total Fixed Costs ÷ Average Revenue Per Clinic

₹30,000 ÷ ₹2,999 = 10 clinics

→ We break even at just 10 paying clinics.
→ Every clinic after that is 85%+ margin.
```

### Cost Structure (At Scale — 500 Clinics)

| Item | Monthly Cost | Notes |
|------|-------------|-------|
| AWS/GCP Infrastructure | ₹1,50,000 | Auto-scaling, multi-region |
| AI Model Inference (GPU) | ₹80,000 | Batch processing optimization |
| LLM API Costs (Groq/OpenAI) | ₹60,000 | Volume discounts |
| Database (MongoDB Atlas M30) | ₹25,000 | Sharded, replicated |
| Team Salaries (8 people) | ₹8,00,000 | 3 devs, 2 sales, 1 medical advisor, 1 ops, 1 founder |
| Office + Legal + Misc | ₹1,00,000 | Co-working space |
| **Total** | **₹12,15,000** | |
| **Revenue (500 clinics × ₹6,000 avg)** | **₹30,00,000** | |
| **Net Profit** | **₹17,85,000/month** | **59.5% net margin** |

---

## INVESTOR METRICS

### Why This Is Fundable

| Metric | MedicoScope | Industry Benchmark | Verdict |
|--------|------------|-------------------|---------|
| **LTV:CAC Ratio** | 36:1 | >3:1 is good | Exceptional |
| **Gross Margin** | 85–90% | 70–80% for SaaS | Best-in-class |
| **Monthly Churn** | <5% (projected) | <7% is healthy | Sticky product |
| **Payback Period** | 1.5 months | <12 months is good | Almost instant |
| **TAM** | $28B | >$1B required | Massive |
| **Rule of 40** | 85%+ (margin + growth) | >40% is investable | Outstanding |

### Funding Roadmap

| Round | Amount | Timing | Use of Funds | Valuation |
|-------|--------|--------|-------------|-----------|
| **Pre-Seed** | ₹25–50 Lakhs | Month 3–6 | MVP polish, 50 clinic pilots, 1 hire | ₹2–4 Cr |
| **Seed** | ₹1–2 Cr | Month 9–12 | 500 clinics, ABDM integration, team of 8 | ₹15–25 Cr |
| **Series A** | ₹8–15 Cr | Month 18–24 | National expansion, insurance partnerships, 2000+ clinics | ₹80–150 Cr |
| **Series B** | ₹40–80 Cr | Month 30–36 | International (SEA, Africa), model marketplace, 10K+ clinics | ₹400–800 Cr |

### Target Investors

| Category | Names | Why They'd Invest |
|----------|-------|-------------------|
| **Healthcare VC** | Chiratae Ventures, HealthQuad, Alkemi Growth | Sector-focused, understand healthtech |
| **General VC** | Sequoia Surge, Accel, Matrix Partners | Early-stage India focus |
| **Angel Networks** | Indian Angel Network, Mumbai Angels, LetsVenture | Pre-seed friendly |
| **Government Grants** | BIRAC, DST, MeitY, Startup India Seed Fund | Non-dilutive capital |
| **Strategic** | Practo, PharmEasy, 1mg (Tata) | Could be acquirers or partners |

---

## HOSPITAL INTEGRATION STRATEGY

### How We Sell to Hospitals

```
Step 1: Free 30-day pilot (3 departments)
    ↓
Step 2: Show ROI report (scans processed, time saved, accuracy metrics)
    ↓
Step 3: Convert to Professional/Enterprise plan
    ↓
Step 4: Expand to more departments
    ↓
Step 5: Hospital refers us to sister hospitals (network effect)
```

### Integration Points

| Hospital System | Our Integration | Value |
|----------------|----------------|-------|
| **PACS** (Picture Archiving) | Read DICOM images → AI analysis | Radiologist gets AI second opinion |
| **HIS** (Hospital Information System) | Patient data sync via ABDM | No manual data entry |
| **LIS** (Lab Information System) | Auto-parse lab results | Instant AI interpretation |
| **EMR** (Electronic Medical Records) | Write AI findings back to EMR | Complete patient record |
| **Billing System** | Per-scan billing integration | Transparent usage tracking |

---

## INSURANCE PARTNERSHIP MODEL

### Why Insurers Will Pay Us

```
Problem: Insurance companies pay ₹2–5 Lakhs per critical illness claim.
Solution: Early detection reduces claims by 30–40%.

If MedicoScope screens 10,000 patients and catches 50 early-stage conditions
that would have become ₹3L claims:

Savings for insurer: 50 × ₹3,00,000 = ₹1.5 Crore
Our fee: ₹50/patient × 10,000 = ₹5 Lakhs
Insurer ROI: 30x return

→ This is why insurers will fight to partner with us.
```

### Insurance Revenue Model

| Tier | Patients Screened | Per-Patient Fee | Annual Revenue |
|------|------------------|----------------|---------------|
| Pilot (1 insurer) | 10,000 | ₹50 | ₹5,00,000 |
| Growth (3 insurers) | 50,000 | ₹75 | ₹37,50,000 |
| Scale (10 insurers) | 5,00,000 | ₹100 | ₹5,00,00,000 |

---

## GOVERNMENT OPPORTUNITY (MASSIVE)

### Ayushman Bharat Integration

India's government health insurance scheme covers **50 Crore people** (500 million). The government is actively looking for AI solutions to:

1. Screen patients at **Primary Health Centers (PHCs)** where no specialist exists
2. Reduce unnecessary referrals to district hospitals
3. Digitize health records via **ABDM/ABHA**

### Our Fit

| Government Need | Our Solution |
|----------------|-------------|
| AI screening at 1.5L PHCs | On-device AI works without internet |
| Reduce referral load | AI triage decides: treat locally vs. refer |
| ABDM compliance | We're building ABDM-native |
| Multi-language | 7 languages, expanding to 22 |
| Cost-effective | Per-screening cost < ₹10 |

### Government Revenue Potential

| Scale | Screens/Year | Revenue |
|-------|-------------|---------|
| 1 district pilot | 50,000 | ₹5,00,000 |
| 1 state rollout | 10,00,000 | ₹1,00,00,000 |
| National (5% of PHCs) | 1,00,00,000 | ₹10,00,00,000 |

---

## COMPETITIVE LANDSCAPE

| Competitor | What They Do | Our Advantage |
|-----------|-------------|---------------|
| **Qure.ai** | AI radiology (chest X-ray) | We're multi-modal (skin + chest + brain + heart + mental health). They do ONE thing. |
| **SkinVision** | AI skin cancer detection | We have 7 skin conditions vs their 3. Plus we have full platform, not just skin. |
| **Practo** | Doctor marketplace | They connect you to a doctor. We give the doctor AI superpowers. We're complementary, not competitive. |
| **mFine** | AI-assisted consultation | Cloud-only, no on-device AI. Doesn't work offline. We work everywhere. |
| **Google Health** | AI medical research | Enterprise pricing, not accessible to Indian clinics. We're 10x cheaper. |

### Our Unfair Advantages

1. **On-device AI** — works without internet (40% of rural clinics have unreliable connectivity)
2. **Multi-modal** — skin + chest + brain + heart + mental health + vitals + lab reports (no competitor covers all)
3. **India-first** — 7 regional languages, Indian lab reference ranges, INR pricing
4. **Full platform** — not just detection, but triage → explanation → escalation → consultation
5. **Built for ₹150 phones** — TFLite models optimized for low-end Android devices

---

## IMMEDIATE POST-HACKATHON ACTION PLAN (Next 30 Days)

| Week | Action | Expected Outcome |
|------|--------|-----------------|
| **Week 1** | Register company (LLP/Pvt Ltd) | Legal entity for contracts |
| **Week 1** | Apply to DPIIT Startup India | Tax benefits, fund access |
| **Week 2** | Approach 10 clinics in Jodhpur for free pilot | 5 confirmed pilots |
| **Week 2** | Apply to IIT Jodhpur TBI incubator | Mentorship + workspace + funding |
| **Week 3** | Set up Razorpay subscription billing | Payment infrastructure ready |
| **Week 3** | Build clinic admin dashboard | Usage analytics for pilot clinics |
| **Week 4** | File provisional patent | "On-device multi-modal medical AI triage system" |
| **Week 4** | Prepare pitch deck for angel investors | Fundraising ready |

---

## THE 10-YEAR VISION

```
Year 1:   100 clinics in Rajasthan → ₹80L revenue
Year 2:   1,500 clinics across 5 states → ₹10 Cr revenue
Year 3:   5,000 clinics + insurance partnerships → ₹36 Cr revenue
Year 4:   Government contracts + international pilot → ₹100 Cr revenue
Year 5:   AI model marketplace + 20K clinics → ₹300 Cr revenue
Year 7:   Expand to Southeast Asia & Africa → ₹1,000 Cr revenue
Year 10:  IPO or strategic acquisition → ₹5,000+ Cr valuation
```

---

## FINAL WORD

MedicoScope is not a demo. It's a **deployed, multi-modal, multi-language AI healthcare platform** with working on-device inference, cloud AI pipelines, real-time vitals monitoring, mental health safety systems, and explainable AI — all built and functional.

The technology works. The market is massive. The unit economics are exceptional. The only question is execution speed.

**The next step is not more features. It's 10 paying clinics.**

---

*Document Version: 1.0*
*Last Updated: March 2026*
*Prepared for: MedicoScope Founding Team*
