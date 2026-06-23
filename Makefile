.PHONY: test test-coverage test-parallel test-fast lint format check

test:
	pytest -v --reuse-db

test-coverage:
	pytest --cov=. --cov-config=.coveragerc --cov-report=html --cov-report=term --reuse-db -v

test-parallel:
	pytest -v -n auto --reuse-db

test-fast:
	pytest -v --reuse-db --no-header -q

lint:
	ruff check apps/ config/

format:
	ruff format apps/ config/

check: lint test-coverage
	@echo "All checks passed!"

coverage-report:
	pytest --cov=. --cov-config=.coveragerc --cov-report=html --cov-report=term --reuse-db
	@echo "HTML coverage report: coverage_html/index.html"

test-accounts:
	pytest apps/accounts/ -v --reuse-db

test-startups:
	pytest apps/startups/ -v --reuse-db

test-matching:
	pytest apps/matching/ -v --reuse-db

test-chat:
	pytest apps/chat/ -v --reuse-db

test-meetings:
	pytest apps/meetings/ -v --reuse-db

test-billing:
	pytest apps/billing/ -v --reuse-db

test-all-modules:
	pytest apps/accounts/ apps/startups/ apps/matching/ apps/chat/ apps/meetings/ apps/investments/ apps/data_room/ apps/notifications/ apps/billing/ apps/operations/ apps/settings/ apps/onboarding/ apps/observability/ apps/analytics/ apps/search_app/ -v --reuse-db

watch:
	pytest-watch -- --reuse-db -v
