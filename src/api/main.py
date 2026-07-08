from fastapi import FastAPI

app = FastAPI(title="AI Lap Simracing API")


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-lap-simracing"}
