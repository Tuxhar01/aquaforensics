You're right. Here is the **entire README in ONE single copy-paste block**. No separate sections outside it.

```markdown
# 🌊 AquaForensics

### Evidence-guided environmental investigation for urban freshwater anomalies

[![Live Demo](https://img.shields.io/badge/Live-Demo-0b5cff)](https://aquaforensics-tushar-kumars-projects-c616a5d2.vercel.app/)
[![Hackathon](https://img.shields.io/badge/IEEE-OneAquaHealth%202026-111827)](https://oneaquahealth.org/)
[![Track](https://img.shields.io/badge/Track-AI--Supported%20Assessment-7c3aed)](https://oneaquahealth.org/)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js-black)](https://nextjs.org/)
[![Language](https://img.shields.io/badge/Python%20%7C%20TypeScript-3776AB)](https://www.python.org/)

> **AquaForensics doesn't ask AI to decide what happened. It asks what evidence we need to find out.**

AquaForensics is an evidence-guided environmental investigation engine that transforms citizen observations of urban freshwater anomalies into structured investigations, competing latent states, uncertainty analysis, and recommendations for the **next-best evidence to collect**.

Built for the **OneAquaHealth IEEE Global Hackathon 2026**, under the **AI-Supported Assessment** track.

---

## 📑 Table of Contents

- [🎯 The Problem](#-the-problem)
- [💡 The Idea](#-the-idea)
- [⚙️ How It Works](#️-how-it-works)
- [🧠 Reasoning Engine](#-reasoning-engine)
- [🔬 Investigation States](#-investigation-states)
- [📐 Expected Information Gain](#-expected-information-gain)
- [👤 Human-in-the-Loop](#-human-in-the-loop)
- [🛡️ Scientific Boundaries](#️-scientific-boundaries)
- [🏗️ Architecture](#️-architecture)
- [🧰 Tech Stack](#-tech-stack)
- [🔄 Investigation Workflow](#-investigation-workflow)
- [🔌 API](#-api)
- [📋 FHIR-Oriented Export](#-fhir-oriented-export)
- [🌍 OneAquaHealth Alignment](#-oneaquahealth-alignment)
- [🎥 Demo](#-demo)
- [🚀 Local Development](#-local-development)
- [🧪 Testing](#-testing)
- [📁 Project Structure](#-project-structure)
- [⚠️ Limitations](#️-limitations)
- [🔭 Future Work](#-future-work)
- [🤖 Responsible AI](#-responsible-ai)
- [🏆 Hackathon](#-hackathon)

---

## 🎯 The Problem

Citizen science can provide valuable observations about urban freshwater ecosystems:

- unusual water colour
- visible turbidity
- suspended sediment
- surface changes
- observations following rainfall
- other locally observed freshwater anomalies

But an observation is only the beginning of an investigation.

A dashboard can display the observation.

A classifier can attempt to assign a label.

The harder question is:

> **What should we observe next to reduce the uncertainty?**

Environmental observations are often incomplete and ambiguous. Several explanations may remain plausible at the same time.

Automatically selecting one explanation from limited evidence can create false certainty.

AquaForensics approaches the problem differently.

---

## 💡 The Idea

AquaForensics treats environmental investigation as an **evidence-selection problem**.

Instead of:

```text
Observation → AI prediction → presumed cause
```

the system follows:

```text
Observation
     ↓
Contextualize
     ↓
Represent competing investigation states
     ↓
Evaluate current uncertainty
     ↓
Compute Expected Information Gain
     ↓
Recommend next-best evidence
     ↓
Human selects / collects evidence
     ↓
Bayesian update
     ↓
Reassess investigation
     ↓
Repeat
```

The goal is not to produce a confident-sounding answer.

The goal is to determine:

> **Which additional observation would be most useful right now?**

---

## ⚙️ How It Works

AquaForensics combines:

- Bayesian updating
- entropy-based reasoning
- Expected Information Gain (EIG)
- feasibility filtering
- observer reliability
- sensitivity analysis
- evidence provenance
- human-in-the-loop decisions
- auditable investigation timelines

The core reasoning engine is deterministic and separate from natural-language explanation.

An LLM is **not** used to generate posterior support, calculate EIG, or determine the investigation state.

---

## 🧠 Reasoning Engine

### Bayesian Updating

AquaForensics maintains competing investigation states and updates their relative model-based support as new evidence is recorded.

Conceptually:

```text
Prior state support
        +
New observation
        ↓
Bayesian update
        ↓
Updated state support
```

Observer reliability is incorporated into evidence updates so that observations with different reliability levels do not necessarily have identical influence.

The resulting values are model outputs under declared assumptions.

They are **not calibrated environmental probabilities**.

---

## 📐 Expected Information Gain

The central question in AquaForensics is not simply:

> "What is the most likely explanation?"

It is:

> **"What evidence would reduce our uncertainty the most?"**

For a candidate action `a`, the prototype computes Expected Information Gain as the expected reduction in entropy:

```text
EIG(a) =
H(current state distribution)
-
E[H(posterior state distribution | observation from a))]
```

where `H` represents entropy.

In practical terms:

> **EIG estimates how much uncertainty a possible observation could remove.**

Candidate actions are evaluated and ranked after feasibility filtering.

The recommendation is therefore computed from the current investigation state rather than being a fixed hard-coded action.

---

## 🔬 Investigation States

The current prototype represents three competing latent investigation states.

### 🌐 W — Reach-wide / Upstream Condition

The evidence is consistent with a condition that may extend across the observed reach or originate upstream, conditional on the anomaly being representative.

### 📍 L — Local Source Condition

The evidence is consistent with a localized source within or near the observed reach, conditional on the anomaly being representative.

### ⏱️ N — Transient / Non-Representative Condition

The observation may represent a transient condition or a non-representative observation.

This state is deliberately **not treated as a causal explanation**.

The three-state representation is an investigation model, not a claim that these are the only possible real-world causes.

---

## 🔎 Candidate Evidence Actions

The current prototype evaluates actions including:

| Action | Purpose |
|---|---|
| `upstream_view` | Compare conditions upstream |
| `recheck_60min` | Re-observe after approximately 60 minutes |
| `second_downstream` | Obtain another downstream observation |
| `inspect_pipes_works` | Inspect nearby pipes or works where feasible |

> ℹ️ The 60-minute recheck is an **AquaForensics investigation protocol**, not an official OneAquaHealth rule.

---

## 👤 Human-in-the-Loop

AquaForensics deliberately does not automate the entire investigation.

The engine can identify an observation with high expected information value, but a human investigator remains responsible for deciding whether and how evidence is collected.

Evidence records can include:

- selected action
- observed outcome
- observer reliability
- elapsed time
- provenance
- source classification

This creates a clear separation between:

```text
🤖 Machine reasoning
```

and:

```text
👤 Human evidence collection and decision-making
```

The system is therefore designed to **support investigation rather than replace the investigator**.

---

## 🛡️ Scientific Boundaries

AquaForensics is intentionally conservative about what it claims.

### ❌ The prototype does not:

- diagnose pollution
- identify a polluter
- prove environmental causality
- determine toxicity
- make medical diagnoses
- provide regulatory enforcement decisions
- claim calibrated real-world probabilities
- treat an LLM-generated explanation as scientific evidence

The current numerical parameters are:

> **Expert-elicited and uncalibrated demonstration parameters.**

Therefore, the support values shown by the prototype represent:

> **Model-based evidence support under declared assumptions.**

They should not be interpreted as validated environmental probabilities.

For example:

```text
Correct interpretation:
"Current evidence favours this investigation state under the model assumptions."

Incorrect interpretation:
"There is a 70% probability that this is the environmental cause."
```

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                     Next.js Frontend                        │
│                                                             │
│  Investigation UI                                          │
│  ├── Observation entry                                     │
│  ├── Competing states                                      │
│  ├── EIG analysis                                          │
│  ├── Candidate actions                                     │
│  ├── Evidence recording                                    │
│  ├── Audit timeline                                        │
│  └── FHIR-oriented export                                  │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              │ REST API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                         │
│                                                             │
│  routers/                                                   │
│  └── investigations.py                                      │
│                                                             │
│  services/                                                  │
│  ├── investigation_service.py                              │
│  ├── engine_service.py                                     │
│  ├── fhir_exporter.py                                      │
│  └── weather_service.py                                    │
│                                                             │
│  Core Engine                                                │
│  ├── Bayesian updating                                      │
│  ├── Entropy calculation                                    │
│  ├── Expected Information Gain                              │
│  ├── Feasibility filtering                                  │
│  ├── Reliability weighting                                  │
│  └── Sensitivity analysis                                   │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
                    SQLite / SQLAlchemy
```

---

## 🧰 Tech Stack

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- Lucide React

### Backend

- Python
- FastAPI
- Pydantic
- SQLite
- HTTPX

### 🧠 Reasoning

- Bayesian inference
- Entropy
- Expected Information Gain
- Sensitivity analysis
- Deterministic decision logic

### 🌦️ Context

- Open-Meteo weather service

### 🔗 Interoperability

- HL7 FHIR R4-oriented structured export

### ☁️ Deployment

- Vercel — frontend
- Render — backend

---

## 🔄 Investigation Workflow

### 1️⃣ Create Investigation

A user starts an investigation from a citizen observation.

The demonstration environment clearly identifies synthetic data.

### 2️⃣ Initial Assessment

The engine represents the competing investigation states and evaluates the current evidence.

When the evidence does not justify selecting one state, the system can return:

```text
NEAR_TIE
```

This is intentional.

The engine does not force a conclusion simply because one is expected.

### 3️⃣ Evaluate Candidate Evidence

The system calculates EIG for feasible evidence-collection actions.

Example from the demonstration engine:

```text
Candidate Action          EIG
--------------------------------
recheck_60min             0.2454 bits
upstream_view             0.2269 bits
second_downstream         0.1702 bits
inspect_pipes_works       0.0588 bits
```

> ⚠️ These values are from the prototype's demonstration scenario. They are not empirically calibrated environmental information values.

### 4️⃣ Human Evidence Collection

The investigator chooses an available action and records the resulting observation.

Example:

```text
Action:
upstream_view

Outcome:
upstream_turbid

Observer reliability:
0.90
```

The observation and associated metadata become part of the investigation record.

### 5️⃣ 🧮 Bayesian Update

The new evidence is incorporated into the reasoning engine.

The investigation is reassessed and a new recommendation is computed.

Completed evidence actions can be excluded from subsequent candidate recommendations.

### 6️⃣ 🔁 Continue the Investigation

The workflow can continue as new evidence becomes available.

Contradictory observations are preserved rather than hidden.

When evidence becomes insufficiently decisive, the investigation can return to:

```text
INSUFFICIENT CONFIDENCE
```

and recommend continued observation or repeat checking.

---

## 🕒 Audit Timeline

Every investigation maintains a chronological record of important events.

A typical investigation can contain:

```text
Investigation Created
        ↓
Assessment Computed
        ↓
Evidence Collection Action
        ↓
Observation Recorded
        ↓
Assessment Updated
        ↓
Recommendation Computed
```

This provides an auditable history rather than exposing only the latest model output.

---

## 🔌 API

The FastAPI backend exposes the investigation workflow through REST endpoints.

Core endpoints include:

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/investigations` | Create an investigation |
| `GET` | `/api/investigations` | List investigations |
| `GET` | `/api/investigations/{id}` | Get investigation details |
| `POST` | `/api/investigations/{id}/observations` | Record evidence |
| `POST` | `/api/investigations/{id}/assess` | Reassess investigation |
| `GET` | `/api/investigations/{id}/recommendation` | Get next-best evidence |
| `POST` | `/api/investigations/{id}/actions/{action_id}/complete` | Complete evidence action |
| `GET` | `/api/investigations/{id}/timeline` | Retrieve audit timeline |
| `GET` | `/api/investigations/{id}/fhir` | Generate structured FHIR-oriented export |
| `GET` | `/health` | Backend health check |

---

## 📋 FHIR-Oriented Export

AquaForensics provides a structured export based on **HL7 FHIR Release 4 concepts**.

The export can represent investigation information, observations, assessments, provenance, and related structured resources.

The prototype deliberately uses the terminology:

> **FHIR-oriented structured export**

Formal conformance to a specific OneAquaHealth FHIR implementation guide or profile is **not claimed** by this prototype.

---

## 🌍 OneAquaHealth Alignment

AquaForensics is designed as an **evidence-guidance and reasoning layer** around citizen observations rather than another generic environmental dashboard.

The project aligns particularly with the:

### **AI-Supported Assessment**

track.

The core workflow is:

```text
Citizen Observation
        ↓
Structured Assessment
        ↓
Competing States
        ↓
Uncertainty Analysis
        ↓
Expected Information Gain
        ↓
Next-Best Evidence
        ↓
Human Decision
        ↓
New Evidence
```

Where applicable, the implementation distinguishes between:

- OneAquaHealth-aligned concepts
- AquaForensics extensions
- unverified mappings

This prevents prototype-specific fields from being presented as official OneAquaHealth standards.

---

## 🎥 Demo

### 🚀 Live Prototype

https://aquaforensics-tushar-kumars-projects-c616a5d2.vercel.app/

### 🎬 Demo Video

_Add the final YouTube/Vimeo link here._

### 💻 Repository

https://github.com/Tuxhar01/aquaforensics

---

## 🚀 Local Development

### Prerequisites

- Python 3.x
- Node.js 18+
- npm

### 1. Clone the repository

```bash
git clone https://github.com/Tuxhar01/aquaforensics.git
cd aquaforensics
```

### 2. Start the FastAPI backend

From the repository root:

```bash
pip install -r requirements.txt
```

Start the server:

```bash
uvicorn main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Health endpoint:

```text
http://127.0.0.1:8000/health
```

### 3. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
```

Create:

```text
.env.local
```

with:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Then run:

```bash
npm run dev
```

The frontend will be available at:

```text
http://localhost:3000
```

---

## 🧪 Testing

The repository contains separate tests for the reasoning engine, backend/API behaviour, and the end-to-end investigation flow.

Run:

```bash
pytest
```

The tests cover areas including:

- Bayesian update behaviour
- entropy calculations
- Expected Information Gain
- candidate action evaluation
- feasibility filtering
- completed-action exclusion
- investigation status transitions
- contradictory evidence
- robustness/sensitivity behaviour
- API validation
- end-to-end investigation flow

The repository also contains a held-out experiment used to evaluate the stability of the implemented model-family behaviour under parameter perturbations.

> ⚠️ Passing the software tests does **not** establish scientific validity of the underlying environmental likelihood assumptions. The tests validate implemented software behaviour and declared model properties.

---

## 📁 Project Structure

```text
aquaforensics/
│
├── 🧠 engine.py
│   └── Core Bayesian + Expected Information Gain engine
│
├── 🔌 adapter.py
│   └── Application/engine adapter
│
├── ⚙️ config.json
│   └── Model assumptions, candidate actions and configuration
│
├── 🗄️ database.py
│   └── SQLite database setup
│
├── 📋 models.py
│   └── Pydantic data models
│
├── 🚀 main.py
│   └── FastAPI application entry point
│
├── routers/
│   └── investigations.py
│       └── Investigation API routes
│
├── services/
│   ├── engine_service.py
│   │   └── Reasoning engine integration
│   │
│   ├── investigation_service.py
│   │   └── Investigation workflow logic
│   │
│   ├── fhir_exporter.py
│   │   └── FHIR-oriented structured export
│   │
│   └── weather_service.py
│       └── Weather/context integration
│
├── 🧪 test_engine.py
│   └── Reasoning engine tests
│
├── 🧪 test_backend.py
│   └── Backend/API tests
│
├── 🧪 test_e2e_flow.py
│   └── End-to-end investigation workflow test
│
├── 🔬 heldout_experiment.py
│   └── Held-out robustness experiment
│
├── 📊 heldout_results_*.json
│   └── Experiment outputs
│
├── frontend/
│   ├── app/
│   │   ├── investigations/
│   │   │   └── [id]/
│   │   │       └── page.tsx
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   │
│   ├── components/
│   │   ├── AuditTimelineModal.tsx
│   │   ├── CandidateActionsList.tsx
│   │   ├── FhirExportModal.tsx
│   │   ├── Navbar.tsx
│   │   ├── RecommendationCard.tsx
│   │   ├── RecordObservationModal.tsx
│   │   ├── ScientificDisclaimer.tsx
│   │   └── StateSupportCard.tsx
│   │
│   ├── lib/
│   │   ├── api.ts
│   │   ├── constants.ts
│   │   └── types.ts
│   │
│   └── package.json
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚠️ Limitations

AquaForensics is currently a **research-oriented hackathon prototype**, not an operational environmental monitoring system.

Important limitations include:

1. Numerical likelihood parameters are expert-elicited and uncalibrated.
2. The current anomaly representation is intentionally narrow.
3. Demonstration observations are synthetic.
4. Real-world environmental datasets have not yet been used to calibrate the likelihood model.
5. Real environmental systems are more complex than the current three-state representation.
6. The current persistence layer uses SQLite.
7. FHIR interoperability is structured, but formal profile conformance remains pending.
8. External data availability can vary by deployment environment.
9. The system does not establish environmental causality from observations.

These limitations are explicitly disclosed rather than hidden behind model output.

---

## 🔭 Future Work

### 1. 📊 Empirical Calibration

Replace expert-elicited likelihood parameters with empirically estimated parameters using validated environmental datasets.

### 2. 🌊 Expanded Anomaly Types

Extend the investigation framework beyond visual water anomalies to support additional structured observation types.

Potential areas include:

- odour
- surface changes
- conductivity-related observations
- temperature anomalies
- rainfall-linked events
- repeated temporal patterns

### 3. 🗺️ Richer Spatial and Temporal Evidence

Integrate additional spatial and temporal environmental data, including:

- citizen observations
- weather
- geospatial datasets
- upstream/downstream measurements
- validated environmental monitoring datasets

### 4. 🔗 Stronger Interoperability

Strengthen interoperability with validated OneAquaHealth/FHIR profiles as implementation requirements become available and verified.

### 5. 📐 Empirical EIG Validation

Evaluate whether actions ranked highly by the model actually provide useful information when tested against real-world observations.

### 6. 🧠 Calibrated Investigation Models

With sufficiently large and validated datasets, future versions could learn calibrated likelihood models while retaining explicit uncertainty and human oversight.

---

## 🤖 Responsible AI

### 🔎 Evidence over explanation

The system prioritizes observable evidence over plausible-sounding explanations.

### 📉 Uncertainty over false precision

Uncertainty is exposed rather than hidden behind confident language.

### 👤 Human oversight

Evidence collection remains a human decision.

### 🧪 Reproducibility

The core reasoning engine is deterministic and testable.

### 🔗 Provenance

Evidence sources, assumptions, and extensions are explicitly represented.

### 🧭 Scientific humility

The prototype does not claim more than its evidence and calibration support.

---

## 🏆 Hackathon

### OneAquaHealth IEEE Global Hackathon 2026

**Track:** AI-Supported Assessment

**Project:** AquaForensics

### Core Concept

> **An evidence-guided environmental investigation engine that turns citizen observations into competing hypotheses, uncertainty analysis, and the next-best evidence to collect.**

---

<div align="center">

## 🌊 AquaForensics

### Evidence first. Decisions human-guided.

Built for the **OneAquaHealth IEEE Global Hackathon 2026**.

</div>
```
