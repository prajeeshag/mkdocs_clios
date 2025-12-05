
# mkdocs_clios

![Test Status](https://github.com/prajeeshag/mkdocs_clios/actions/workflows/test.yml/badge.svg)
![PyPI - Version](https://img.shields.io/pypi/v/mkdocs_clios)
[![codecov](https://codecov.io/gh/prajeeshag/mkdocs_clios/graph/badge.svg?token=UNNUW30IQL)](https://codecov.io/gh/prajeeshag/mkdocs_clios)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
---

**mkdocs_clios** is a MkDocs plugin that generates Markdown documentation for [Clios](https://github.com/prajeeshag/clios) operators.

## Installation
```bash
$ pip install mkdocs_clios
```

## Usage
In `mkdocs.yml` file add the following:
```yaml
plugins:
    - mkdocs_clios:
        app: path_clios_app:app # path to clios app
```
