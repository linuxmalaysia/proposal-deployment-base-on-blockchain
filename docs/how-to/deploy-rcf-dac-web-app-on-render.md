---
okf_version: "0.2"
type: "howto"
title: "Deploying the RCF & DAC Interactive Web Application on Render.com"
timestamp: "2026-08-28T00:00:00Z"
topics: ["render-com", "deployment", "fastapi", "python-runtime", "troubleshooting", "rcf", "dac"]
description: "Step-by-step Diátaxis How-To guide for building, configuring, deploying, and troubleshooting the RCF & DAC interactive web service on Render.com using FastAPI and uv."
resource: "file:///docs/how-to/deploy-rcf-dac-web-app-on-render.md"
sources: [
  "https://render.com/docs/troubleshooting-python-deploys",
  "https://linuxmalaysia.github.io/proposal-deployment-base-on-blockchain/",
  "render.yaml",
  "pyproject.toml"
]
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-28T00:00:00Z"
language: "en-GB"
---

# 🚀 Deploying the RCF & DAC Interactive Web Application on Render.com

This guide provides a comprehensive step-by-step walkthrough for deploying the **Research Commercialisation Fund (RCF) & Digital Asset Custodian (DAC)** interactive Python web application to [Render.com](https://render.com/).

---

## 🎯 Python Web Framework Architecture Recommendation

To operationalise the interactive web components demonstrated on the [RCF & DAC Portal](https://linuxmalaysia.github.io/proposal-deployment-base-on-blockchain/), **FastAPI** is selected as the recommended Python framework:

1. **High Performance & Asynchronous:** Built on Starlette and Pydantic, providing sub-millisecond response latency.
2. **Built-in Data Validation:** Enforces strict types for DID user registration, file hashing payloads, Cloverleaf MRS score calculations, and revenue-split calculations.
3. **Automatic OpenAPI/Swagger Documentation:** Interactive test suite available natively at `/docs`.
4. **Seamless Render Integration:** Operates directly with Uvicorn or Gunicorn on Render's native Python 3 runtime using `uv`.

---

## 📋 Prerequisites & Project Structure

Ensure the repository contains the following deployment artifacts:

```
.
├── render.yaml                             # Render Blueprint specification
├── pyproject.toml                          # Dependency manifest (fastapi, uvicorn, pydantic)
├── uv.lock                                 # UV lockfile required by Render native uv support
└── src/
    └── dca_service/
        └── web_app.py                      # FastAPI application entry point
```

---

## 🛠️ Deployment Step-by-Step Instructions

### Method 1: Render Blueprint Deployment (Recommended)

1. Push your changes to GitHub or GitLab.
2. Log into the [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** and select **Blueprint**.
4. Connect your repository containing `render.yaml`.
5. Render will automatically detect `render.yaml` and configure the web service with:
   - **Build Command:** `uv sync`
   - **Start Command:** `uvicorn src.dca_service.web_app:app --host 0.0.0.0 --port $PORT`
   - **Python Version:** `3.12.13`

---

### Method 2: Manual Web Service Setup on Render

If creating the web service manually in the Render Dashboard:

1. Click **New +** -> **Web Service**.
2. Select your repository.
3. Set the following parameters:
   - **Runtime:** `Python 3`
   - **Build Command:** `uv sync`
   - **Start Command:** `uvicorn src.dca_service.web_app:app --host 0.0.0.0 --port $PORT`
4. Under **Environment Variables**, add:
   - `PYTHON_VERSION`: `3.12.13`

---

## 🔧 Troubleshooting Render Python Deploys

Based on [Render's Official Troubleshooting Guide](https://render.com/docs/troubleshooting-python-deploys), common deployment issues and resolutions include:

### 1. Incorrect Runtime
- **Symptom:** Build fails with `command not found: uv` or missing Python tools.
- **Resolution:** Verify in service Settings that the runtime is set to **Python 3** (or Docker if deploying via container).

### 2. Incompatible Python Version
- **Symptom:** Deploy logs show `Current Python version (3.11.10) is not allowed by the project (^3.12)` or `SyntaxError: invalid syntax`.
- **Resolution:** Set the `PYTHON_VERSION` environment variable in the Render Dashboard to `3.12.13` matching `pyproject.toml`.

### 3. Missing Dependencies or Missing UV Lockfile
- **Symptom:** Deploy logs show `ModuleNotFoundError: No module named 'fastapi'` or `uv.lock file missing`.
- **Resolution:** Ensure both `pyproject.toml` and `uv.lock` are committed in the repository root. When `uv.lock` is present, Render natively runs `uv sync`.

### 4. Port Binding Errors
- **Symptom:** Service fails health checks or times out during deployment startup.
- **Resolution:** Ensure the start command binds to `0.0.0.0` and uses the `$PORT` environment variable supplied by Render:
  ```bash
  uvicorn src.dca_service.web_app:app --host 0.0.0.0 --port $PORT
  ```

---

## 🌐 Endpoints & Verification

Once deployed, verify your service endpoints:

- **Web Application Portal:** `https://<your-service>.onrender.com/`
- **Health Check:** `https://<your-service>.onrender.com/health`
- **Interactive OpenAPI Specs:** `https://<your-service>.onrender.com/docs`
- **W3C DID Registration API:** `POST /api/register-user`
- **Asset Evidence Vault Hash API:** `POST /api/register-asset`
- **Cloverleaf MRS Calculator API:** `POST /api/calculate-cloverleaf`
- **Revenue Distribution Calculator API:** `POST /api/calculate-revenue`
- **Investor Data Room API:** `GET /api/investor-assets`
