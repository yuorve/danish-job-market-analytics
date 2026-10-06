.PHONY: help install demo-data pipeline test dashboard docker-build docker-up clean

PYTHON := python3

help:
	@echo "Danish Job Market Analytics - Makefile commands:"
	@echo "  make demo-data    : Generate 520+ realistic synthetic Danish IT job listings"
	@echo "  make pipeline     : Execute Extract -> Clean -> Transform -> Load pipeline"
	@echo "  make test         : Run automated test suite across all modules"
	@echo "  make dashboard    : Launch Streamlit web dashboard on port 8501"
	@echo "  make docker-build : Build containerized image"
	@echo "  make docker-up    : Launch container with docker-compose"
	@echo "  make clean        : Remove temporary test files and caches"

demo-data:
	$(PYTHON) scripts/generate_demo_data.py

pipeline:
	$(PYTHON) -m src.pipeline

test:
	$(PYTHON) -m unittest discover tests -v

dashboard:
	streamlit run dashboard/app.py

docker-build:
	docker compose build

docker-up:
	docker compose up

clean:
	rm -rf __pycache__ .pytest_cache tests/__pycache__ src/**/__pycache__
