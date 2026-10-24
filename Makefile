# Toutes les commandes se lancent depuis la racine du projet.
.PHONY: install models index index-dev eval api ui test test-ollama lint scenarios

install:            ## dépendances verrouillées (uv.lock)
	uv sync

models:             ## modèles Ollama retenus (~7,3 Go)
	ollama pull qwen3.5:9b
	ollama pull qwen3-embedding:0.6b

index:              ## index principal : 4 000 décisions (~1 h d'embeddings sur M5)
	uv run jurirag-build --n 4000 --index-name main

index-dev:          ## petit index pour essayer vite (~5 min)
	uv run jurirag-build --n 300 --index-name dev-small

eval:               ## évaluation du retrieval (BM25 / dense / hybride)
	uv run jurirag-eval --n 150 --index-name main

api:                ## service API  -> http://127.0.0.1:8000/docs
	uv run jurirag-api

ui:                 ## interface    -> http://localhost:8501
	uv run streamlit run services/ui/src/jurirag_ui/app.py

test:               ## tests sans Ollama (LLM scripté)
	uv run pytest

test-ollama:        ## tests d'intégration avec le vrai modèle (Ollama démarré, index construit)
	uv run pytest -m ollama -o addopts=""

lint:
	uv run ruff check services scripts && uv run ruff format --check services scripts && uv run mypy

scenarios:          ## rejoue les 3 scénarios de test et enregistre leurs traces (API démarrée)
	uv run python scripts/run_scenarios.py
