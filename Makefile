.PHONY: install install-voice run test clean help

# Detecta el gestor de paquetes disponible: uv > pip
UV := $(shell command -v uv 2>/dev/null)

install:
ifdef UV
	uv tool install . --force
else
	pip install -e .
endif

install-voice:
ifdef UV
	uv tool install ".[voice]" --force
else
	pip install -e ".[voice]"
endif

run:
ifdef UV
	adv-archon
else
	python -m adv_archon
endif

test:
ifdef UV
	uv run pytest tests/ -v
else
	pytest tests/ -v
endif

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

help:
	@echo "Comandos disponibles:"
	@echo "  make install        — Instala Archon (detecta uv o pip automáticamente)"
	@echo "  make install-voice  — Instala también los módulos de voz (Whisper + pyttsx3)"
	@echo "  make run            — Inicia Archon"
	@echo "  make test           — Ejecuta los tests"
	@echo "  make clean          — Limpia archivos compilados"
	@echo ""
	@echo "Atajo rápido (si ya instalaste con uv): adv-archon  o  adv"
