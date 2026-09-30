from fastapi import FastAPI

app = FastAPI(
    title="BIST Katılım AI Predictor",
    version="0.1.0",
    description="AI destekli BIST Katılım tahmin sistemi",
)


@app.get("/")
def root():
    return {
        "status": "ok",
        "application": "BIST Katılım AI Predictor",
        "version": "0.1.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "backend",
    }
