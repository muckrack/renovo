.DEFAULT_GOAL := dist

.PHONY: clean
clean:
	$(RM) dist/*

.PHONY: dist
dist:
	flit build

requirements-test.txt: pyproject.toml
	UV_CUSTOM_COMPILE_COMMAND='make $@' \
	uv pip compile \
		--extra test \
		--no-emit-index-url \
		--output-file $@ \
		--python-version 3.11 \
		--quiet \
		$(PIP_COMPILE_ARGS) \
		pyproject.toml

.PHONY: lint
lint:
	ruff format --check src/ tests/
	ruff check src/ tests/

.PHONY: test
test:
	PYTHONPATH=./tests pytest -v -s
