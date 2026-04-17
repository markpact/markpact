# Sample FastAPI Notebook

This notebook demonstrates a simple FastAPI application converted to markpact.

## Uruchomienie

```bash
markpact README.md
```

---

```text markpact:deps python
fastapi
pydantic
uvicorn
```

```python markpact:file path=app.py
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float
    description: str = ""

app = FastAPI(title="Sample API")

items = []

@app.get("/")
def root():
    return {"message": "Hello from Notebook!"}

@app.get("/items")
def list_items():
    return items

@app.post("/items")
def add_item(item: Item):
    items.append(item)
    return item
```

```bash markpact:run
uvicorn app:app --host 0.0.0.0 --port ${MARKPACT_PORT:-8000}
```
