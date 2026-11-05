# Campus Customs

Yale SOM MGT 409 homework. The shop desk, the five agents, and both database files are in this repo.

`data/campus_customs.db` is the original shop. `data/campus_customs_new.db` is the working copy the app reads and writes. `POST /reset` copies the original over the working copy.

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Put your own Portkey key in `.env`. That file is gitignored and is not in this repo.

```bash
cd frontend
npm install
```

## Run

From `backend/`:

```bash
uvicorn main:app --reload --port 8000
```

From `frontend/`:

```bash
npm run dev
```

The desk is at http://localhost:5173 and calls http://localhost:8000.
