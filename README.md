# 🚀 Emad (عماد) | Multi-Source Job & Internship Discovery Engine

<div align="center">

> *"قول إنت بتدور على إيه.. وعماد هيتصرف"*  
> **Stop juggling tabs across job portals. Emad aggregates, classifies, and deduplicates opportunities across LinkedIn and regional Arab job networks into one clean dashboard.**

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Beautiful Soup](https://img.shields.io/badge/Beautiful_Soup-4.12-4B8BBE?style=for-the-badge)](https://pypi.org/project/beautifulsoup4/)
[![Status](https://img.shields.io/badge/Status-Active-2ea043?style=for-the-badge)]()
[![Platform](https://img.shields.io/badge/Target-Egypt_·_Saudi_·_UAE-orange?style=for-the-badge)]()

</div>

---

## 💡 What is Emad?

**Emad** is an intelligent, lightweight **Multi-Source Job Discovery Engine** designed specifically for job seekers, students, and professionals in **Egypt 🇪🇬, Saudi Arabia 🇸🇦, and the UAE 🇦🇪**.

Instead of manually checking multiple sites every day, getting bombarded with irrelevant leads, or seeing the exact same job reposted five times under slightly different titles, **Emad orchestrates the entire discovery process autonomously**:
1. **Discovers** listings across independent sources (**LinkedIn** and **Tanqeeb**).
2. **Classifies** seniority, contract types, and work environments using title-first rules.
3. **Hard-Filters** out irrelevant roles before they ever reach your screen.
4. **Deduplicates** cross-source duplicates using a conservative multi-signal confidence engine.
5. **Ranks** results by relevance and presents them with direct apply links and source badges.

> **Zero accounts, zero logins, zero API credentials required.** Emad uses clean, public, and stable guest endpoints.

---

## ⚙️ Engine Pipeline Architecture

```text
               1. Discovery & Extraction
      ┌─────────────────────────┴────────────────────────┐
      ▼                                                  ▼
LinkedIn (Guest Search)                       Tanqeeb (Regional Network)
   [Egypt · Saudi · UAE]                          [Egypt · Saudi · UAE]
      │                                                  │
      └─────────────────────────┬────────────────────────┘
                                ▼
                    2. Data Normalization
               (Clean strings, URLs, legal suffixes)
                                ▼
                    3. Strict Classification
            (Seniority · Job Type · Workplace Environment)
                                ▼
                    4. Hard Filtering Gate
          (Rejects unqualified roles, senior mismatches, etc.)
                                ▼
                 5. Multi-Signal Deduplication
               (Merges duplicates into: LinkedIn · Tanqeeb)
                                ▼
                    6. Relevance Ranking
               (Weighted scoring: 0–100 match rating)
                                ▼
                    7. Modern UI Presentation
          (Interactive job cards, direct apply buttons, CSV export)
```

---

## 🌟 Key Features

### 1. 🌐 True Multi-Source Discovery
- **LinkedIn Integration (`LinkedInSource`):** Guest job search targeting relevant postings across MENA and globally.
- **Tanqeeb Regional Network (`TanqeebSource`):** Automatic subdomain routing tailored to the user's selected country:
  - **Egypt 🇪🇬:** Routed to `egypt.tanqeeb.com` (Cairo, Alexandria, Mansoura, Giza, etc.)
  - **Saudi Arabia 🇸🇦:** Routed to `saudi.tanqeeb.com` (Riyadh, Jeddah, Dammam, Mecca, etc.)
  - **United Arab Emirates 🇦🇪:** Routed to `uae.tanqeeb.com` (Dubai, Abu Dhabi, Sharjah, etc.)
  - **Gulf & MENA:** Supports Kuwait, Qatar, Oman, Bahrain, and Jordan.
- **Fault-Isolated Execution:** If one source experiences a temporary network hiccup, the other source continues seamlessly without crashing or surfacing stack traces.

---

### 2. 🛡️ Intelligent Multi-Signal Deduplication (`dedup.py`)
> **Core Principle: "A false merge is far worse than an undetected duplicate."**

Emad avoids naive `company + title` merges that hide real jobs. Instead, it uses a multi-signal confidence engine:
- **Canonical URL Matching:** Cleans and normalizes URLs by stripping tracking queries (`utm_*`, `ref`, `trk`).
- **Conservative Company Normalization:** Strips *only* pure legal suffixes (`LLC`, `Ltd`, `Inc`, `Corp`, `ش.م.م`). Crucial corporate identity tokens like `Technologies`, `Solutions`, `Systems`, and `Labs` are strictly preserved (e.g., *Smart Eye* and *Smart Eye Technologies* remain separate).
- **Location Guardrails:** Same company and title in different cities (e.g., Cairo vs. Alexandria) are strictly kept as **2 separate jobs**.
- **Smart Merging:** When verified as identical, the card is merged with dual badges (`✨ LinkedIn · Tanqeeb`) and points to the best direct application link.

---

### 3. 🎯 High-Precision Filtering (Zero False Positives)
- **Hard-Gated Internship Filter:** When searching for internships or training programs:
  - Rejects any leadership or senior title (`Senior`, `Lead`, `Staff`, `Architect`, `Director`, `Manager`, `Head`).
  - Rejects postings with explicit experience requirements (e.g., `1–2 years`, `2+ yrs`, `خبرة 3 سنوات`).
  - Excludes cross-domain noise (e.g., Marketing or HR roles when searching for Software).
- **Smart Intent Normalization:** Typing `Flutter intern` automatically extracts the core skill (`Flutter`) and sets the seniority filter to `Internship`, preventing conflicting dork queries.
- **Seniority Tiers:**
  - `الكل (أي مستوى)` - All levels
  - `تدريب طلبة وخريجين (Internship)` - Pure internships and graduate programs
  - `مبتدئ / حديث تخرج (Junior / Entry)` - Entry-level roles, blocking senior and 3+ years requirements
  - `متوسط الخبرة (Mid-Level)` - Mid-level opportunities
  - `سينيور / خبير (Senior / Lead)` - Senior, Lead, and Architect roles
  - `إدارة وقيادة (Manager / Director)` - Departmental and executive management
- **Workplace Environments:** Remote (`عن بُعد`), Hybrid (`هجين`), or On-site (`من المقر`).

---

### 4. 🎨 Modern Dark Theme Interface
- **Responsive RTL UI:** Styled with Google Cairo typography, glowing accent borders, and glassmorphic filter controls.
- **Live Source Badges:**
  - `LinkedIn` (Classic Blue)
  - `Tanqeeb (تنقيب)` (Emerald Green)
  - `✨ LinkedIn · Tanqeeb` (Gradient Purple for merged multi-source opportunities)
- **Dynamic Apply Buttons:** Automatically adapts text based on the source (`قدّم على LinkedIn ↗`, `قدّم على Tanqeeb ↗`, or `قدّم على الرابط المباشر ↗`).
- **Arabic Excel / CSV Export:** One-click download with `UTF-8 with BOM` encoding for seamless Arabic text display in Microsoft Excel.

---

## 📁 Project Structure

```text
job-scaraping/
├── app.py                      # Streamlit interactive application & modern UI
├── scraper.py                  # JobDiscoveryEngine coordinator & JobClassifier
├── dedup.py                    # Multi-signal deduplication & false-merge protection
├── sources/                    # Modular source adapters
│   ├── __init__.py             # Source registry exports
│   ├── base.py                 # UnifiedJob data model & BaseJobSource interface
│   ├── linkedin.py             # LinkedIn guest scraping adapter
│   └── tanqeeb.py              # Tanqeeb regional multi-country adapter (Egypt, Saudi, UAE)
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

---

## 🚀 Quick Start (Local Setup)

### 1. Clone the Repository
```bash
git clone https://github.com/0xQenawy/job-scrabbing.git
cd job-scaraping
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the App
```bash
streamlit run app.py
```

Open your browser at **`http://localhost:8501`**, specify your target role, pick your country/city, and let Emad do the work!

---

## 🗺️ Supported Geographic Coverage

| Country | Coverage Highlights |
|---|---|
| **Egypt 🇪🇬** | Cairo, Giza, Alexandria, Mansoura / Dakahlia, Tanta, Zagazig, Canal Cities, Upper Egypt, Red Sea, etc. |
| **Saudi Arabia 🇸🇦** | Riyadh, Jeddah, Eastern Province (Dammam / Khobar), Mecca, Medina, etc. |
| **UAE 🇦🇪** | Dubai, Abu Dhabi, Sharjah, Ajman, etc. |
| **Custom / Worldwide 🌍** | Support for any custom city or international search. |

---

## 💡 Tips for Best Results
- **Looking for Internships?** Enter just the core technology (e.g. `Flutter` or `React`) and select `تدريب طلبة وخريجين (Internship)` from the seniority dropdown. Emad will filter out all senior noise and experienced roles automatically.
- **Multiple Roles:** Search for multiple related titles at once separated by commas (e.g. `Frontend, React, Web`).
- **Direct Application:** Clicking the apply button opens the original direct application page without passing through unneeded redirects.

---

<div align="center">
Built with ❤️ for every job hunter in the Arab world.
</div>
