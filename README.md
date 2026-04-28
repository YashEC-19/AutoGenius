# 🚗 AutoGenius — Unified Automotive Intelligence Platform

> **Multi-Agent AI | Multimodal GenAI | Kubernetes Deployment**
> Built with: CrewAI · LangChain · Groq · Pollinations.ai · Laravel · Minikube

---

## 📁 Project Structure

```
autogenius/
├── agents/                  # Project 1 — CrewAI Multi-Agent System
│   ├── langchain_tools.py   #   STEP 2: LangChain prompt tools
│   ├── researcher_agent.py  #   STEP 3: Researcher Agent
│   ├── writer_agent.py      #   STEP 4: Writer Agent
│   ├── crew_orchestrator.py #   STEP 5: Crew + handoff logic
│   └── requirements.txt
│
├── vision/                  # Project 2 — Multimodal Pipeline
│   ├── langchain_vision_chain.py   # STEP 8: Text narrative chain
│   ├── image_generator.py          # STEP 9: Pollinations integration
│   ├── multimodal_pipeline.py      # STEP 10: Combined pipeline
│   └── requirements.txt
│
├── laravel-app/             # Project 3 — PHP Laravel App
│   └── ...                  #   STEP 11
│
├── docker/                  # Project 3 — Containerization
│   ├── Dockerfile           #   STEP 12
│   └── docker-compose.yml
│
├── k8s/                     # Project 3 — Kubernetes
│   ├── deployment.yaml      #   STEP 13
│   ├── service.yaml
│   ├── configmap.yaml
│   └── rolling-update.sh    #   STEP 14
│
├── outputs/                 # Generated reports, images (runtime)
├── config.py                # Central config loader
├── setup_check.py           # Environment verification
├── requirements.txt         # Master requirements
├── .env.example             # Environment template
└── README.md                # This file
```

---

## 🚀 Quick Start

### Step 1 — Clone & Setup Environment

```bash
# Navigate into the project
cd autogenius

# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

### Step 2 — Configure API Keys

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Groq API key
# Get free key at: https://console.groq.com
```

Open `.env` and set:
```
GROQ_API_KEY=gsk_your_actual_key_here
```

### Step 3 — Verify Setup

```bash
python setup_check.py
```

You should see all green checkmarks ✅

---

## 🤖 Project 1 — Multi-Agent System

```bash
cd agents

# Run the full crew pipeline
python crew_orchestrator.py --car "Tesla Model S Plaid"

# Output saved to: outputs/report_<timestamp>.json
#                  outputs/report_<timestamp>.md
```

**Agent Flow:**
```
Researcher Agent  ──(JSON specs)──►  Writer Agent  ──►  Formatted Report
```

---

## 🎨 Project 2 — Multimodal Pipeline

```bash
cd vision

# Generate text narrative + car image
python multimodal_pipeline.py --prompt "Futuristic electric SUV with solar panels"

# Output: Console narrative + image saved to outputs/
```

---

## ☸️ Project 3 — Laravel on Kubernetes

```bash
# Build Docker image
cd docker
docker build -t autogenius-laravel:v1 .

# Start Minikube
minikube start

# Deploy to Kubernetes
kubectl apply -f ../k8s/

# Access the app
minikube service autogenius-service

# Perform rolling update
bash ../k8s/rolling-update.sh
```

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| LLM Inference | Groq (Llama 3.3 70B) | Ultra-fast AI responses |
| Agent Framework | CrewAI 0.80 | Multi-agent orchestration |
| LLM Chaining | LangChain 0.3 | Prompt templates, chains |
| Image Generation | Pollinations.ai | Free text-to-image API |
| Web Framework | Laravel 11 (PHP) | Automotive showcase app |
| Containerization | Docker | App packaging |
| Orchestration | Kubernetes (Minikube) | Local K8s deployment |
| Zero-Downtime | Rolling Updates | Seamless version transitions |

---

## 📋 Build Steps Progress

- [x] STEP 1 — Project structure + requirements + config
- [ ] STEP 2 — LangChain tools + prompt templates
- [ ] STEP 3 — Researcher Agent
- [ ] STEP 4 — Writer Agent
- [ ] STEP 5 — Crew Orchestrator
- [ ] STEP 6 — Agent output format
- [ ] STEP 7 — End-to-end agent test
- [ ] STEP 8 — LangChain vision chain
- [ ] STEP 9 — Pollinations image generation
- [ ] STEP 10 — Combined multimodal output
- [ ] STEP 11 — Laravel app
- [ ] STEP 12 — Docker + compose
- [ ] STEP 13 — K8s manifests
- [ ] STEP 14 — Rolling update script
- [ ] STEP 15 — React dashboard

---

## 📄 License
MIT — Built for educational and professional demonstration purposes.
