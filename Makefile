REPOS := gps wingfoil

.PHONY: install setup test lint all

## Install Claude skills and set up all repos
install:
	./install.sh

## Regenerate root requirements.txt from uv.lock
requirements:
	uv export --no-hashes --output-file requirements.txt

setup:
	@for repo in $(REPOS); do \
		echo "→ setting up $$repo"; \
		if [ ! -f $$repo/.env ] && [ -f $$repo/.env.example ]; then \
			cp $$repo/.env.example $$repo/.env; \
			echo "  created $$repo/.env from .env.example"; \
		fi; \
		cd $$repo && uv sync --group dev && uv run pre-commit install && cd ..; \
	done
	@echo "→ smoke test: verifying imports"
	@for repo in $(REPOS); do \
		echo "  $$repo: import fastmcp"; \
		cd $$repo && uv run python -c "import fastmcp; print(f'  fastmcp {fastmcp.__version__} OK')" && cd ..; \
	done

## Run tests across all repos
test:
	@for repo in $(REPOS); do \
		echo "→ testing $$repo"; \
		cd $$repo && uv run pytest --cov --cov-fail-under=100 && cd ..; \
	done

## Run pre-commit on all repos
lint:
	@for repo in $(REPOS); do \
		echo "→ linting $$repo"; \
		cd $$repo && uv run pre-commit run --all-files && cd ..; \
	done

all: setup test lint
