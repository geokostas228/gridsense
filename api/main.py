from fastapi import FastAPI

from routers.billing import router as billing_router

app = FastAPI(
    title="GridSense API",
    version="1.0.0"
)

app.include_router(billing_router)

@app.get("/")
def root():
    return {
        "message": "GridSense API is running"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }