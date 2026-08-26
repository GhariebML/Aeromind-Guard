# AeroMind ClimateGuard — Enterprise Deployment Guide

## 1. Prerequisites
- **Operating System**: Ubuntu 22.04 LTS / Debian 12 / Windows Server 2022
- **Container Engine**: Docker 24.0+ & Docker Compose v2.20+
- **GPU (Optional)**: NVIDIA Driver 535+ & NVIDIA Container Toolkit (for CUDA acceleration)
- **Node.js**: Node 18+ (for local frontend development)
- **Python**: Python 3.10 to 3.14

---

## 2. Environment Configuration (`.env`)

Create a `.env` file from `.env.example`:

```bash
# Application Mode (production or demo)
APP_MODE=production

# Database Configuration (PostgreSQL for production)
DATABASE_URL=postgresql://aeromind:secure_password_here@postgres:5432/aeromind_db

# FortyGuard Environmental Intelligence API
FORTYGUARD_API_KEY=your_production_api_key_here
FORTYGUARD_BASE_URL=https://api.fortyguard.com/v1

# AI & LLM Engine
OLLAMA_URL=http://ollama:11434
COPILOT_MODEL=llama3

# Server Settings
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

---

## 3. Deployment with Docker Compose

To launch the full production stack:

```bash
# 1. Build and launch all services in detached mode
docker-compose up --build -d

# 2. Verify container health status
docker-compose ps

# 3. Stream centralized system logs
docker-compose logs -f backend
```

---

## 4. Production Service Verification

- **API Health Check**:
  ```bash
  curl -i http://localhost:8000/api/v1/health
  # Response: HTTP 200 {"status": "HEALTHY", "version": "1.0.0", "app_mode": "production"}
  ```

- **System Diagnostics**:
  ```bash
  curl -s http://localhost:8000/api/v1/system/status | jq
  ```

- **Access Operator Command Center**:
  Navigate to `http://localhost:3000` (or `http://localhost:5173` if running Vite dev server).
