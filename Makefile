.PHONY: install install-voice run test clean help

install:
	pip install -e .

install-voice:
	pip install -e ".[voice]"

run:
	python -m adv_archon

test:
	pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

help:
	@echo "Comandos disponibles:"
	@echo "  make install        — Instala Archon y sus dependencias"
	@echo "  make install-voice  — Instala también los módulos de voz (Whisper + pyttsx3)"
	@echo "  make run            — Inicia Archon"
	@echo "  make test           — Ejecuta los tests"
	@echo "  make clean          — Limpia archivos compilados"
