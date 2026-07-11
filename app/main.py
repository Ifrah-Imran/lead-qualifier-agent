from fastapi import FastAPI

app = FastAPI(title="Lead Qualifier Agent")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/enrich")
def enrich():
    return {
        "status": "placeholder",
        "message": "Lead enrichment endpoint stub",
        "data": {},
    }


@app.post("/score")
def score():
    return {
        "status": "placeholder",
        "message": "Lead scoring endpoint stub",
        "score": None,
    }


@app.post("/draft")
def draft():
    return {
        "status": "placeholder",
        "message": "Draft generation endpoint stub",
        "draft": "",
    }


@app.post("/log")
def log():
    return {
        "status": "placeholder",
        "message": "Activity logging endpoint stub",
        "logged": False,
    }
