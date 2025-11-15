import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, EmailStr

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Contact(BaseModel):
    name: str
    email: EmailStr
    message: str


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.post("/api/contact")
def submit_contact(payload: Contact):
    # Try to persist to MongoDB if available, otherwise just acknowledge
    saved = False
    try:
        from database import create_document
        doc_id = create_document("contact", payload)
        saved = True
        return {"ok": True, "saved": saved, "id": doc_id}
    except Exception:
        # Fallback: pretend saved (no DB configured in this environment)
        return {"ok": True, "saved": False}


@app.get("/api/resume")
def download_resume(type: str | None = None):
    base = os.path.join(os.path.dirname(__file__), "static")
    mapping = {
        None: ("Sparsh_Resume.pdf", "Sparsh — Resume"),
        "aiml": ("Sparsh_Resume_AIML.pdf", "Sparsh — AIML Resume"),
        "web": ("Sparsh_Resume_Web.pdf", "Sparsh — Web Resume"),
    }
    fname, download_name = mapping.get(type, mapping[None])
    fpath = os.path.join(base, fname)
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="Resume not found")
    return FileResponse(fpath, media_type="application/pdf", filename=f"{download_name}.pdf")


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        # Try to import database module
        from database import db

        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except ImportError:
        response["database"] = "❌ Database module not found"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
