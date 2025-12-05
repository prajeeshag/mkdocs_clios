#!/usr/bin/env bash

set -ex

uv run mypy mkdocs_clios
uv run ruff check mkdocs_clios tests
uv run ruff format --check mkdocs_clios tests
