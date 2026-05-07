# Backend Quick Start

## 1) Create virtual environment

```powershell
python -m venv .venv
```

## 2) Activate virtual environment

```powershell
.\.venv\Scripts\activate
```

## 3) Install dependencies

```powershell
pip install -r requirements.txt
```

## 4) Start API server

```powershell
uvicorn app.main:app --reload
```

## 5) API docs

Open: http://127.0.0.1:8000/docs

## 6) v0.2 HTTP Runner Notes

- `target_type` supports: `prompt`, `agent_http`, `rag_http`
- `prompt` keeps mock behavior and does not call external HTTP.
- `agent_http` / `rag_http`:
  - If `endpoint_url` is empty: fallback to mock response.
  - If `endpoint_url` is not empty: run real HTTP request via Python `urllib`.
- `method` supports `POST` and `GET` (default `POST`).
- `headers_json` should be a JSON object string.
- `body_template` is used for `POST` and supports `{input_text}` replacement.
- `GET` appends `input_text` as query parameter.
- Errors are returned as `HTTP_ERROR: ...` and stored into test result reason.
