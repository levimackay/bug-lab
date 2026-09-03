PY=.venv/bin/python

setup:            ## create venvs, install deps, install frontend deps
	uv venv -q --python /opt/homebrew/bin/python3.14 .venv
	uv pip install -q -p .venv/bin/python -e ".[dev]"
	uv venv -q --python /opt/homebrew/bin/python3.14 var/py
	uv pip install -q -p var/py/bin/python pytest
	ln -sf "$$(xcrun --find clang)" var/py/bin/cc && ln -sf "$$(xcrun --find clang)" var/py/bin/clang
	cd frontend && npm install --no-audit --no-fund

dev:              ## backend on :8000 and frontend on :5173
	@trap 'kill 0' INT TERM; \
	.venv/bin/uvicorn server.main:app --port 8000 --reload --reload-dir server --reload-dir engine & \
	cd frontend && npm run dev; wait

serve:            ## production: build the frontend and serve everything from :8000
	cd frontend && npm run build
	.venv/bin/uvicorn server.main:app --port 8000

test:             ## engine + server tests
	$(PY) -m pytest -q

verify:           ## every incident really breaks and really fixes, plus tests, typecheck, lint
	$(PY) scripts/verify_incidents.py
	$(PY) -m pytest -q
	cd frontend && npm run build && npm run lint

.PHONY: setup dev serve test verify
