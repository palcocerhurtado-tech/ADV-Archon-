install:
	pip install -e .

test:
	pytest tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
