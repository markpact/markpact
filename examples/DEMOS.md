# markpact Demo Live

Interaktywne demo, które generuje kompletny projekt z promptu LLM i tworzy profesjonalną dokumentację PDF w czasie rzeczywistym.

## 🚀 Szybki start

```bash
# Instalacja zależności
pip install markpact[llm] fpdf2

# Interaktywne menu z wyborem promptu
python demos/demo_live.py

# Uruchom demo z własnym promptem
python demos/demo_live.py --prompt "Build a chat API with WebSocket"

# Użyj gotowego przykładu
python demos/demo_live.py --example todo-api

# Lista dostępnych przykładów
python demos/demo_live.py --list
```

## 📋 Co robi demo?

### 1. Generowanie kontraktu z LLM
- Wysyła prompt do skonfigurowanego LLM (Ollama/OpenRouter/OpenAI)
- Generuje kompletny README.md z blokami `markpact:*`
- Czas generowania: 30-90 sekund

### 2. Parsowanie bloków markpact:*
- Analizuje wygenerowany README.md
- Wyodrębnia bloki: `markpact:deps`, `markpact:file`, `markpact:run`, `markpact:test`
- Waliduje wymagane bloki

### 3. Analiza zawartości
- **Zależności**: Liczy pakiety i języki
- **Pliki**: Analizuje rozmiar i hash SHA-256
- **Komendy**: Ekstrahuje komendy uruchomieniowe
- **Testy**: Liczy asercje testowe

### 4. Integralność SHA-256
- Oblicza hash każdego bloku
- Weryfikuje integralność danych
- Zapisuje do PDF

### 5. Generowanie PDF
- Tworzy 7-stronicowy dokument PDF
- Strona tytułowa z metadanymi
- Podsumowanie generowania
- Szczegóły każdego bloku
- Hashy SHA-256

## 📁 Struktura wyjściowa

```
generated/live/
├── README.md              # Wygenerowany kontrakt
└── markpact_live_custom.pdf  # Dokumentacja PDF
```

## 🎛️ Konfiguracja LLM

Konfiguracja przez zmienne środowiskowe (plik `.env` lub `export`):

### Ollama (lokalny, domyślny)
```bash
export MARKPACT_MODEL=ollama/qwen2.5-coder:14b
export MARKPACT_API_BASE=http://localhost:11434
```

### OpenRouter (chmura)
```bash
export MARKPACT_MODEL=openrouter/google/gemini-2.0-flash-001
export MARKPACT_API_KEY=sk-or-v1-xxxxx
```

### OpenAI
```bash
export MARKPACT_MODEL=gpt-4o-mini
export MARKPACT_API_KEY=sk-xxxxx
```

### Anthropic
```bash
export MARKPACT_MODEL=claude-3-5-haiku-20241022
export MARKPACT_API_KEY=sk-ant-xxxxx
```

### Override modelu jednorazowo
```bash
python demos/demo_live.py --example todo-api --model openrouter/google/gemini-2.0-flash-001
```

## 📊 Przykładowe wyjście

Poniżej rzeczywiste wyjście z `--example calculator-api` (Ollama qwen2.5-coder:14b):

```
========================================================================
  markpact -- Live Contract Generation
========================================================================

  >>>  Prompt:  calculator-api
  >>>  Model:   ollama/qwen2.5-coder:14b
  >>>  API:     http://localhost:11434

========================================================================
  KROK 1: Generowanie kontraktu przez LLM
========================================================================

  [....] Oczekiwanie na odpowiedz LLM...  [PASS]
  [PASS] LLM wygenerował kontrakt  110130ms, 2424 znaków
  [PASS] README.md zapisany  generated/live/README.md

========================================================================
  KROK 2: Parsowanie blokow markpact:*
========================================================================

  [PASS] Znaleziono 4 blokow  0.1ms
  [PASS] markpact:deps  lang=text, 24 chars
  [PASS] markpact:file=app/main.py  lang=python, 1269 chars
  [PASS] markpact:run  lang=bash, 65 chars
  [PASS] markpact:test  lang=text, 480 chars

========================================================================
  KROK 3: Walidacja wymaganych blokow
========================================================================

  [PASS] markpact:deps -- obecny
  [PASS] markpact:file -- obecny
  [PASS] markpact:run -- obecny
  [PASS] markpact:test -- obecny (opcjonalny)
        markpact:target -- brak (opcjonalny)

  [PASS] Walidacja: PASS -- wszystkie wymagane bloki obecne

========================================================================
  KROK 4: Analiza zawartosci blokow
========================================================================

  [PASS] Zaleznosci: 3 pakietow  fastapi, uvicorn, pydantic
  [PASS] Plik: app/main.py  40 linii, sha256=9f685f803975
  [PASS] Run command: uvicorn app.main:app --host 0.0.0.0 --port ${MARKPACT_PORT:-8000}
  [PASS] Testy: 7 assercji

========================================================================
  KROK 5: Integralnosc -- SHA-256
========================================================================

  [PASS] README.md SHA-256: bed014a73c6e624045593636...
  [PASS] markpact:deps SHA-256: 1ef577a673407cd0
  [PASS] markpact:file=app/main.py SHA-256: 9f685f803975437c
  [PASS] markpact:run SHA-256: b49cce15b5712fdd
  [PASS] markpact:test SHA-256: 09a96da7f4c2379a

========================================================================
  PODSUMOWANIE
========================================================================

  Prompt:      calculator-api
  Model:       ollama/qwen2.5-coder:14b
  Czas:        110.2s
  Bloki:       4 markpact:*
  Walidacja:   10 passed / 0 failed / 10 total

  [PASS] PDF zapisany: generated/live/markpact_live_calculator_api.pdf  13 KB, 7 stron
  [PASS] README.md: generated/live/README.md

  ============================================================
    Kontrakt gotowy! 4 blokow z 1 promptu.
  ============================================================
```

## 🔧 Dostępne opcje

```bash
python demos/demo_live.py --help

options:
  -h, --help            show this help message and exit
  --prompt, -p PROMPT   Custom prompt text
  --example, -e EXAMPLE Use predefined example prompt (e.g. todo-api)
  --list, -l            List available example prompts
  --model, -m MODEL     Override LLM model
```

## 📝 Przykłady promptów

### REST API
```bash
python demos/demo_live.py --prompt "REST API for task management with SQLite"
```

### WebSocket API
```bash
python demos/demo_live.py --prompt "Chat API with WebSocket support"
```

### CLI Tool
```bash
python demos/demo_live.py --prompt "Command-line tool for file processing"
```

### Web Dashboard
```bash
python demos/demo_live.py --prompt "Streamlit dashboard for data visualization"
```

## 🛠️ Wymagania techniczne

- Python 3.8+
- `markpact[llm]` - LLM integracja (litellm)
- `fpdf2` - PDF generation
- Dostęp do LLM API (Ollama/OpenRouter/OpenAI)

## 🐛 Troubleshooting

### Brak LLM — fallback mode
```
[WARN] litellm nie zainstalowane. LLM fallback bedzie uzyty.
```
Demo działa w trybie fallback (minimalny README). Dla pełnej generacji:
```bash
pip install markpact[llm]
```

### Brak PDF
```
[FAIL] fpdf2 nie zainstalowane -- brak PDF
```
```bash
pip install fpdf2
```

### Konflikt PyFPDF/fpdf2
```
UserWarning: You have both PyFPDF & fpdf2 installed.
```
```bash
pip uninstall pypdf && pip install --upgrade fpdf2
```

### Ollama nie dostępne
```
Connection error: http://localhost:11434
```
Uruchom Ollama lokalnie lub przełącz na chmurę:
```bash
# OpenRouter (darmowe modele dostępne)
export MARKPACT_MODEL=openrouter/google/gemini-2.0-flash-001
export MARKPACT_API_KEY=sk-or-v1-xxxxx
python demos/demo_live.py --example todo-api
```

## 🎯 Następne kroki

1. **Uruchom wygenerowany projekt**:
   ```bash
   markpact generated/live/README.md
   ```

2. **Modyfikuj kontrakt**:
   ```bash
   # Edytuj wygenerowany README
   $EDITOR generated/live/README.md
   # Uruchom ponownie
   markpact generated/live/README.md
   ```

3. **Wygeneruj inny projekt**:
   ```bash
   python demos/demo_live.py --example blog-api
   python demos/demo_live.py --prompt "GraphQL API for e-commerce"
   ```

4. **Integracja z marksync** (multi-agent sync):
   ```bash
   marksync server generated/live/README.md
   marksync agent --role editor --name agent-1
   ```

---

## 📁 Pliki wyjściowe

| Plik | Opis |
|------|------|
| `generated/live/README.md` | Wygenerowany kontrakt markpact |
| `generated/live/markpact_live_<name>.pdf` | Dokumentacja PDF (7 stron) |

---

## 📄 Licencja

Demo jest częścią projektu markpact — Apache License 2.0
