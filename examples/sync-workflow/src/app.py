from fastapi import FastAPI

app = FastAPI(title="Sync Demo")

@app.get("/")
def root():
    return {"status": "ok"}
