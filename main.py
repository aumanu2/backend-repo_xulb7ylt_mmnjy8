import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Event, Ticketpurchase

app = FastAPI(title="24 MILA BACI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utilities

def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")


def serialize(doc):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc


# Routes
@app.get("/")
def root():
    return {"message": "24 MILA BACI API running"}

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
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

# Event CRUD
@app.get("/api/events", response_model=List[dict])
def list_events():
    events = get_documents("event")
    return [serialize(e) for e in events]

class EventCreate(Event):
    pass

@app.post("/api/events", status_code=201)
def create_event(event: EventCreate):
    event_id = create_document("event", event)
    return {"id": event_id}

@app.get("/api/events/{event_id}")
def get_event(event_id: str):
    doc = db["event"].find_one({"_id": to_object_id(event_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Event not found")
    return serialize(doc)

class EventUpdate(BaseModel):
    title: Optional[str] = None
    date: Optional[str] = None
    dj: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    image: Optional[str] = None

@app.put("/api/events/{event_id}")
def update_event(event_id: str, payload: EventUpdate):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        return {"updated": False}
    res = db["event"].update_one({"_id": to_object_id(event_id)}, {"$set": updates})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"updated": res.modified_count > 0}

@app.delete("/api/events/{event_id}")
def delete_event(event_id: str):
    res = db["event"].delete_one({"_id": to_object_id(event_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"deleted": True}

# Ticket purchase
class PurchaseRequest(BaseModel):
    buyer_name: str
    email: EmailStr
    phone: Optional[str] = None
    event_id: str
    quantity: int = Field(..., ge=1)

@app.post("/api/tickets/purchase")
def purchase_ticket(req: PurchaseRequest):
    event = db["event"].find_one({"_id": to_object_id(req.event_id)})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    total = float(event.get("price", 0)) * req.quantity
    purchase_doc = {
        "buyer_name": req.buyer_name,
        "email": req.email,
        "phone": req.phone,
        "event_id": req.event_id,
        "quantity": req.quantity,
        "total_price": total,
    }
    purchase_id = create_document("ticketpurchase", purchase_doc)
    return {"id": purchase_id, "total_price": total, "event_title": event.get("title")}

# Simple admin authentication via env token
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

class AdminEvent(BaseModel):
    title: str
    date: str
    dj: str
    price: float
    description: Optional[str] = None
    image: Optional[str] = None

@app.post("/api/admin/events")
def admin_add_event(event: AdminEvent, token: str):
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    event_id = create_document("event", event)
    return {"id": event_id}

@app.put("/api/admin/events/{event_id}")
def admin_edit_event(event_id: str, payload: EventUpdate, token: str):
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return update_event(event_id, payload)

@app.delete("/api/admin/events/{event_id}")
def admin_delete_event(event_id: str, token: str):
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return delete_event(event_id)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
