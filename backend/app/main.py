from fastapi import FastAPI

app = FastAPI(title="Bandhan")


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "running", "project": "Bandhan", "version": "1.0"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}
