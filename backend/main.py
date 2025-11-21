import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional

from database import create_document, get_documents, db
from schemas import StepLog, User

app = FastAPI(title="Step Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Step Tracker Backend is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# Utility to transform Mongo docs to safe JSON

def serialize_doc(doc):
    d = dict(doc)
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    return d


# Response models
class StepEntryOut(BaseModel):
    id: str
    user: str
    steps: int
    date: date
    note: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LeaderboardRow(BaseModel):
    user: str
    total_steps: int


@app.post("/api/steps", response_model=dict)
def add_steps(log: StepLog):
    """Create a new step log for a user and date"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    inserted_id = create_document("steplog", log)
    return {"id": inserted_id}


@app.get("/api/steps", response_model=List[StepEntryOut])
def list_steps(user: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None, limit: int = 50):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    query = {}
    if user:
        query["user"] = user
    if start_date and end_date:
        query["date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["date"] = {"$gte": start_date}
    elif end_date:
        query["date"] = {"$lte": end_date}

    docs = get_documents("steplog", query, limit)
    return [serialize_doc(d) for d in docs]


@app.get("/api/leaderboard", response_model=List[LeaderboardRow])
def leaderboard(start_date: Optional[date] = None, end_date: Optional[date] = None, limit: int = 10):
    """Aggregate total steps per user within date range"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    match = {}
    if start_date and end_date:
        match["date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        match["date"] = {"$gte": start_date}
    elif end_date:
        match["date"] = {"$lte": end_date}

    pipeline = []
    if match:
        pipeline.append({"$match": match})
    pipeline += [
        {"$group": {"_id": "$user", "total_steps": {"$sum": "$steps"}}},
        {"$sort": {"total_steps": -1}},
        {"$limit": limit},
        {"$project": {"user": "$_id", "total_steps": 1, "_id": 0}}
    ]

    results = list(db["steplog"].aggregate(pipeline))
    # Ensure types are JSON-compatible
    return [LeaderboardRow(user=r["user"], total_steps=int(r["total_steps"])) for r in results]


@app.post("/api/users", response_model=dict)
def create_user(user: User):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    inserted_id = create_document("user", user)
    return {"id": inserted_id}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
