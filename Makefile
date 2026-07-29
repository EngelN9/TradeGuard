UV ?= uv

.PHONY: setup format lint typecheck test test-unit test-property test-integration
.PHONY: test-contract test-replay test-e2e test-connected evidence dev-up dev-down
.PHONY: api worker web build schemas

setup:
	$(UV) sync --locked
	npm ci --prefix web
	$(UV) run pre-commit install

format:
	$(UV) run ruff format .

lint:
	$(UV) run ruff check .
	$(UV) run python scripts/validate_workflows.py
	$(UV) run python scripts/scan_secrets.py

typecheck:
	$(UV) run mypy
	npm run check --prefix web

test:
	$(UV) run pytest -m "not connected" --cov=tradeguard --cov-report=term-missing --cov-report=xml:artifacts/evidence/bootstrap/tests/coverage.xml --junitxml=artifacts/evidence/bootstrap/tests/all.xml
	npm test --prefix web

test-unit:
	$(UV) run pytest -m unit --junitxml=artifacts/evidence/bootstrap/tests/unit.xml

test-property:
	$(UV) run pytest -m property --junitxml=artifacts/evidence/bootstrap/tests/property.xml

test-integration:
	$(UV) run pytest -m integration --junitxml=artifacts/evidence/bootstrap/tests/integration.xml

test-contract:
	$(UV) run pytest -m contract --junitxml=artifacts/evidence/bootstrap/tests/contract.xml

test-replay:
	$(UV) run pytest -m replay --junitxml=artifacts/evidence/bootstrap/tests/replay.xml

test-e2e:
	npm test --prefix web

test-connected:
	@if [ "$$TRADEGUARD_RUN_CONNECTED" != "1" ]; then \
		echo "SKIP: set TRADEGUARD_RUN_CONNECTED=1 after provider approval"; \
	else \
		$(UV) run pytest -m connected tests/connected; \
	fi

evidence:
	$(UV) run python scripts/collect_evidence.py

schemas:
	$(UV) run python scripts/export_schemas.py

dev-up:
	docker compose up --build -d

dev-down:
	docker compose down

api:
	$(UV) run tradeguard api

worker:
	$(UV) run tradeguard worker

web:
	npm run dev --prefix web

build:
	$(UV) build
	npm run build --prefix web
