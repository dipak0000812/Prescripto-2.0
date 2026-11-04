# Prescripto 2.0 — Render Deployment Guide

This guide details how to deploy Prescripto 2.0 (FastAPI Backend, PostgreSQL Database, Background Worker, and React/Vite Frontend) to [Render](https://render.com).

---

## Architecture on Render

```
                                      +--------------------------+
                                      |     Render Static Site   |
                                      |      (prescripto-web)    |
                                      +------------+-------------+
                                                   |
                                                   | HTTPS (API Requests)
                                                   v
+--------------------------+          +--------------------------+
|  Render Background Worker | <------> |     Render Web Service   |
|    (prescripto-worker)   |          |    (prescripto-backend)  |
+------------+-------------+          +------------+-------------+
             |                                     |
             |       SQLAlchemy (psycopg2)         |
             +-----------------+-------------------+
                               |
                               v
                  +--------------------------+
                  |  Render Managed Postgres |
                  |      (prescripto-db)     |
                  +--------------------------+
```

---

## Method 1: Automated Blueprint Deployment (Recommended)

A complete `render.yaml` blueprint has been added to the root of the project.

### Steps:
1. **Push your code to GitHub / GitLab**:
   ```bash
   git add .
   git commit -m "Prepare Prescripto 2.0 for Render deployment"
   git push origin main
   ```
2. **Open Render Dashboard**:
   - Go to [dashboard.render.com](https://dashboard.render.com).
   - Click **New +** and select **Blueprint**.
3. **Connect Repository**:
   - Select your repository (`Prescripto-2.0`).
   - Render will detect `render.yaml` and configure:
     - `prescripto-db` (PostgreSQL Database)
     - `prescripto-backend` (FastAPI Web Service)
     - `prescripto-worker` (Async Python Worker)
     - `prescripto-web` (React Vite Static Site)
4. **Fill in Environment Secrets**:
   Render will prompt for unset secret variables:
   - `GEMINI_API_KEY`: Your Google AI Studio Gemini API Key.
   - `JWT_PRIVATE_KEY`: Your RS256 Private Key (found in `backend/.env`).
   - `JWT_PUBLIC_KEY`: Your RS256 Public Key (found in `backend/.env`).
5. **Click Apply**:
   - Render provisions the database, runs database migrations (`alembic upgrade head`), seeds 117 canonical medications, creates default admin user, starts the API, starts the worker, and builds the frontend.

---

## Method 2: Manual Step-by-Step Setup in Render Dashboard

If you prefer setting up each service manually without the Blueprint:

### Step 1: Create PostgreSQL Database
1. In Render Dashboard, click **New +** -> **PostgreSQL**.
2. **Name**: `prescripto-db`
3. **Database**: `prescripto_db`
4. **User**: `prescripto`
5. **Region**: Oregon (or your preferred region)
6. **Plan**: Free
7. Click **Create Database**.
8. Once provisioned, copy the **Internal Database URL** (e.g. `postgres://prescripto:...@dpg-.../prescripto_db`).

---

### Step 2: Deploy Backend Web Service (`prescripto-backend`)
1. Click **New +** -> **Web Service**.
2. Connect your Git repository.
3. Configure the service:
   - **Name**: `prescripto-backend`
   - **Language / Runtime**: `Python 3`
   - **Region**: Same as database (Oregon)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && alembic upgrade head && python scripts/seed_medications.py && python scripts/create_user.py
     ```
   - **Start Command**:
     ```bash
     uvicorn prescripto.api.main:app --host 0.0.0.0 --port $PORT
     ```
4. **Environment Variables**:
   Add the following variables under the **Environment** tab:
   | Key | Value | Description |
   | :--- | :--- | :--- |
   | `DATABASE_URL` | *(Paste Internal Database URL from Step 1)* | Automatically normalized to `postgresql+psycopg2://` |
   | `ENVIRONMENT` | `production` | Production mode |
   | `LOG_LEVEL` | `INFO` | Structured logging |
   | `RECOGNITION_PROVIDER` | `gemini` | Gemini Vision OCR & Extraction |
   | `GEMINI_MODEL` | `gemini-3.5-flash` | Primary Vision Model |
   | `GEMINI_FALLBACK_MODEL`| `gemini-3.1-flash-lite` | Quota/rate-limit fallback |
   | `GEMINI_API_KEY` | `your_gemini_api_key` | From Google AI Studio |
   | `JWT_PRIVATE_KEY` | `-----BEGIN PRIVATE KEY-----\n...` | From `backend/.env` |
   | `JWT_PUBLIC_KEY` | `-----BEGIN PUBLIC KEY-----\n...` | From `backend/.env` |
   | `CORS_ORIGINS` | `*` | Or your frontend URL |
5. **Health Check Path**: `/api/v1/health`
6. Click **Create Web Service**.
7. Once deployed, note your backend URL (e.g., `https://prescripto-backend.onrender.com`).

---

### Step 3: Deploy Background Worker (`prescripto-worker`)
1. Click **New +** -> **Background Worker**.
2. Connect your Git repository.
3. Configure:
   - **Name**: `prescripto-worker`
   - **Runtime**: `Python 3`
   - **Region**: Same as database (Oregon)
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m prescripto.worker.main`
4. Add the exact same **Environment Variables** as the Backend Web Service (`DATABASE_URL`, `GEMINI_API_KEY`, `JWT_PRIVATE_KEY`, `JWT_PUBLIC_KEY`, etc.).
5. Click **Create Background Worker**.

---

### Step 4: Deploy Frontend Static Site (`prescripto-web`)
1. Click **New +** -> **Static Site**.
2. Connect your Git repository.
3. Configure:
   - **Name**: `prescripto-web`
   - **Branch**: `main`
   - **Root Directory**: `web`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`
4. **Environment Variables**:
   - `VITE_API_BASE_URL`: `https://prescripto-backend.onrender.com/api/v1` *(Replace with your actual backend URL from Step 2)*
5. **Redirects/Rewrites**:
   - Go to the **Redirects / Rewrites** tab.
   - Click **Add Rule**:
     - **Type**: `Rewrite`
     - **Source**: `/*`
     - **Destination**: `/index.html`
6. Click **Create Static Site**.

---

## Default Production Credentials

When the build command runs `python scripts/create_user.py`, it initializes the administrator account:
- **Email**: `admin@prescripto.local`
- **Password**: `AdminPass123!`
- **Role**: `ADMIN`

*(You can customize this password after logging in or set arguments in `scripts/create_user.py`)*

---

## Verifying Deployment
1. Visit `https://<your-backend-url>/api/v1/health`. You should receive:
   ```json
   {
     "database": "ok",
     "object_storage": "ok",
     "worker_heartbeat": "ok"
   }
   ```
2. Open your frontend URL `https://<your-web-url>.onrender.com`.
3. Test patient OTP login or doctor/admin login with `admin@prescripto.local` / `AdminPass123!`.

