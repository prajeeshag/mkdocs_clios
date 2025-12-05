# type: ignore
import pytest
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files

from mkdocs_clios.plugin import CliosMkDocsPlugin


def test_invalid_app(tmp_path):
    plugin = CliosMkDocsPlugin()
    plugin.config = {"app": "dummy.invalid_app:app"}
    cfg = MkDocsConfig()
    cfg.load_dict({"docs_dir": str(tmp_path)})
    with pytest.raises(ValueError, match="Invalid app: should be an instance of Clios"):
        plugin.on_config(cfg)


def test_on_files_generates_docs(tmp_path, monkeypatch):
    plugin = CliosMkDocsPlugin()
    plugin.config = {"app": "dummy.app:app"}

    cfg = MkDocsConfig()
    cfg.load_dict({"docs_dir": str(tmp_path)})
    plugin.on_config(cfg)

    # force known output
    monkeypatch.setattr(plugin, "_render_markdown_for_operator", lambda *a: "DOC")

    files = Files([])

    plugin.on_files(files, config=cfg)

    generated = list((tmp_path / "operators").glob("*.md"))
    assert len(generated) >= 1
    assert generated[0].name == "dummy_operator.md"
    assert generated[0].read_text() == "DOC"


class DummyParser:
    def get_details(self, *a, **kw):
        return (
            "xcdo add a b",  # synopsis
            "Short description",  # short
            "Long description",  # long
            [  # args_doc
                {
                    "name": "a",
                    "type": "int",
                    "required": "yes",
                    "default": "-",
                    "description": "first arg",
                    "choices": "-",
                }
            ],
            [],  # kwds_doc
        )


class DummyParserNoDetails:
    def get_details(self, *a, **kw):
        return (
            "xcdo add a b",  # synopsis
            "",
            "",
            [],  # kwds_doc
            [  # args_doc
                {
                    "name": "a",
                    "type": "int",
                    "required": "yes",
                    "default": "-",
                    "description": "first arg",
                    "choices": "-",
                }
            ],
        )


class DummyOpFn:
    examples = [("ex1", "xcdo add 1 2")]


class DummyOpFnNoEx:
    examples = []


def test_render_markdown_for_operator():
    plugin = CliosMkDocsPlugin()
    p = DummyParser()
    op = DummyOpFn()

    md = plugin._render_markdown_for_operator("add", op, p)

    assert "# `add`" in md
    assert "## Synopsis" in md
    assert "xcdo add a b" in md
    assert "## Description" in md
    assert "Short description" in md
    assert "Long description" in md
    assert "| `a` | int | yes | -" in md
    assert "## Examples" in md
    assert "xcdo add 1 2" in md


def test_render_markdown_for_operator_no_details():
    plugin = CliosMkDocsPlugin()
    p = DummyParserNoDetails()
    op = DummyOpFnNoEx()

    md = plugin._render_markdown_for_operator("add", op, p)

    assert "# `add`" in md
    assert "## Synopsis" in md
    assert "xcdo add a b" in md
    assert "## Description" not in md
    assert "Short description" not in md
    assert "Long description" not in md
    assert "| `a` | int | yes | -" in md
    assert "## Examples" not in md
    assert "xcdo add 1 2" not in md


def test_render_param_table():
    rows = [
        {
            "name": "x",
            "type": "float",
            "required": "no",
            "default": "1.0",
            "description": "value",
            "choices": "-",
        }
    ]

    md = CliosMkDocsPlugin._render_param_table(rows)

    assert "| `x` | float | no | 1.0 | value | - |" in md
