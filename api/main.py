from fastapi import FastAPI

app = FastAPI(
    title="Travel Order Resolver API",
    description="API pour résoudre les ordres de voyage",
    version="0.1.0",
)


@app.get("/")
def read_root():
    return {"message": "Hello World"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
