# Ardhja

Albanian agritourism marketplace — farms, wineries, and rural experiences.

## Structure

```
ardhja/
├── backend/        # FastAPI application
└── frontend/       # Next.js application (coming later)
```

## Backend quick start

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # edit as needed

alembic upgrade head            # create/migrate database
uvicorn app.main:app --reload   # start dev server
```

API docs: http://localhost:8000/docs
