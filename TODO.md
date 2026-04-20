# TODO – Markpact

## ✅ Zrealizowane

- [x] Testy jednostkowe dla parsera codeblocków
- [x] Flaga `--dry-run` – podgląd bez wykonywania
- [x] Konwerter Markdown → Markpact (`--convert`, `--auto`)
- [x] CLI z pełnymi opcjami
- [x] Dokumentacja (docs/, examples/)
- [x] Publikacja na PyPI (Makefile + .pypirc)
- [x] Generowanie z LLM (`-p "prompt"`, `-e example`)
- [x] Konfiguracja LLM (`markpact config --provider`)
- [x] Docker sandbox (`--docker`)
- [x] HTTP testing (`markpact:test http`)
- [x] Multi-registry publishing (PyPI, npm, Docker)
- [x] Dynamic license mapping for PyPI classifiers
- [x] CLI entry point for published packages
- [x] Full README as PyPI project description
- [x] Examples test script (`scripts/test_examples.sh`)
- [x] New examples: PHP CLI, React TypeScript SPA, TypeScript Node API
- [x] Enhanced auto-fix with LLM integration (`--auto-fix-llm`)
- [x] Automatic dependency addition for ModuleNotFoundError
- [x] Notebook converter (Jupyter, R Markdown, Quarto, Databricks, Zeppelin)

## 🎯 Priorytety

### P0 – Krytyczne
- [ ] Walidacja `path=` (zabezpieczenie przed path traversal `../`)

### P1 – Ważne
- [ ] Obsługa `markpact:deps node` (generowanie `package.json`, `npm install`)
- [ ] Obsługa `markpact:deps system` (apt/brew)
- [ ] Lepsze komunikaty błędów (kolorowe, z numerem linii w README)

### P2 – Nice to have
- [ ] `markpact:config` – ustawienia projektu (port, sandbox path, env vars)
- [ ] `markpact:test` – uruchamianie testów po `markpact:run`
- [ ] `markpact:ignore` – bloki ignorowane przez runtime
- [ ] Watch mode (`--watch`) – przeładowanie przy zmianie README
- [ ] Wsparcie dla Windows (ścieżki `.venv\Scripts\`)

---

## 🔧 Minimalizacja kodu bootstrap

### Obecny stan: ~47 linii

### Możliwe redukcje

| Zmiana | Oszczędność | Uwagi |
|--------|-------------|-------|
| Usunięcie `MARKPACT_NO_VENV` | ~2 linie | Mniej elastyczności |
| Inline `run()` w `main()` | ~5 linii | Gorsza czytelność |
| Usunięcie pretty-print `[markpact]` | ~3 linie | Gorszy UX |
| Jeden regex `p[1]` bez walidacji | ~2 linie | Mniej bezpieczne |
| Lambda zamiast `run()` | ~3 linie | Mniej czytelne |

### Wersja ultra-minimalna (~30 linii)

```python
#!/usr/bin/env python3
import os,re,subprocess,sys;from pathlib import Path
R,S=Path(sys.argv[1] if len(sys.argv)>1 else"README.md"),Path(os.environ.get("MARKPACT_SANDBOX","./sandbox"))
S.mkdir(parents=True,exist_ok=True)
def x(c):subprocess.check_call(c,shell=True,cwd=S,env={**os.environ,**({"PATH":f"{S/'.venv/bin'}:{os.environ.get('PATH','')}"}if(S/".venv/bin").exists()else{})})
d,r=[],None
for m in re.finditer(r"^```(?P<lang>\w+)\s+markpact:(?P<kind>\w+)(?:\s+(?P<meta>[^\n]+))?\n(?P<body>.*?)\n^```",R.read_text(),re.DOTALL|re.MULTILINE):
 k,t,b=m.groups();t,b=(t or"").strip(),b.strip()
 if k=="file":f=S/re.search(r"path=(\S+)",t)[1];f.parent.mkdir(parents=True,exist_ok=True);f.write_text(b)
 elif k=="deps"and"python"in t:d+=[l.strip()for l in b.splitlines()if l.strip()]
 elif k=="run":r=b
if d:(S/"requirements.txt").write_text("\n".join(d));v=S/".venv/bin/pip";v.exists()or x(f"{sys.executable} -m venv .venv");x(f"{v} install -r requirements.txt")
r and x(r)
```

> ⚠️ **Nie rekomendowane** – trudne w utrzymaniu, brak walidacji, brak komunikatów.

---

## 📦 Architektura pakietu Python

```
markpact/
├── src/
│   └── markpact/
│       ├── __init__.py      # wersja, eksport
│       ├── cli.py           # entry point CLI
│       ├── parser.py        # parsowanie codeblocków
│       ├── runner.py        # run(), ensure_venv()
│       └── sandbox.py       # zarządzanie sandboxem
├── tests/
│   ├── test_parser.py
│   └── test_runner.py
├── pyproject.toml
├── Makefile
├── README.md
└── CHANGELOG.md
```

---

## 🚀 Roadmap

- **v0.1** – MVP (zrealizowane)
- **v0.2** – Pakiet pip, CLI `markpact run README.md` (zrealizowane)
- **v0.3** – LLM generation, Docker sandbox, HTTP testing (zrealizowane)
- **v0.4** – Multi-registry publishing, examples test script (zrealizowane)
- **v0.5** – Watch mode, kolorowe logi, path traversal validation
- **v1.0** – Stabilne API, pełna dokumentacja, wszystkie języki
