# mypy: disable-error-code=no-untyped-call
import importlib
import typing as t
from pathlib import Path

from clios import Clios
from clios.core.main_parser import ParserAbc
from clios.core.operator_fn import OperatorFn
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files


class CliosMkDocsPlugin(BasePlugin):  # type: ignore
    """
    Auto-generate Markdown documentation for clios operators.
    """

    def on_config(self, config: MkDocsConfig, **kwargs: t.Any) -> MkDocsConfig:
        # Where to write generated pages
        path = self.config["app"]
        module_name, attr = path.split(":")
        module = importlib.import_module(module_name)
        self.app: Clios = getattr(module, attr)
        if not isinstance(self.app, Clios):
            raise ValueError("Invalid app: should be an instance of Clios")
        self.output_dir = Path(config.docs_dir) / "operators"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return config

    def on_files(self, files: Files, *, config: MkDocsConfig) -> Files:
        """
        Called before MkDocs collects files.
        We generate .md files and let MkDocs see them as part of docs/.
        """
        self._generate_operator_docs()
        return files

    # ------------------------------------------------------------------
    # Render markdown similar to print_detail()
    # ------------------------------------------------------------------
    def _generate_operator_docs(self) -> None:
        parser = self.app._parser
        operators = self.app._operators

        for name, op_fn in operators.items():
            md = self._render_markdown_for_operator(name, op_fn, parser)
            path = self.output_dir / f"{name}.md"
            path.write_text(md, encoding="utf-8")
            print(f"[cli-docs] Generated {path}")  # noqa T201

    # ------------------------------------------------------------------
    def _render_markdown_for_operator(
        self, name: str, op_fn: OperatorFn, parser: ParserAbc
    ) -> str:
        synopsis, short, long, args_doc, kwds_doc = parser.get_details(
            name, op_fn, exe_name="xcdo"
        )
        # Build Markdown -----------------------------------------------
        out = []
        out.append(f"# `{name}`")
        out.append("")
        out.append("## Synopsis")
        out.append("```bash")
        out.append(synopsis)
        out.append("```")
        out.append("")

        if short or long:
            out.append("## Description")
            if short:
                out.append(f"**{short}**")
            if long:  # pragma: no cover
                out.append("")
                out.append(long)
            out.append("")

        if args_doc:
            out.append("## Positional Arguments")
            out.append(self._render_param_table(args_doc))
            out.append("")

        if kwds_doc:
            out.append("## Keyword Arguments")
            out.append(self._render_param_table(kwds_doc))
            out.append("")

        examples = [ex for _, ex in op_fn.examples]
        if examples:
            out.append("## Examples")
            out.append("```bash")
            out.append("\n".join(examples))
            out.append("```")
            out.append("")

        return "\n".join(out)

    # ------------------------------------------------------------------
    @staticmethod
    def _render_param_table(rows: list[dict[str, str]]) -> str:
        header = "| Name | Type | Required | Description |"
        sep = "|------|------|----------|---------------------|"
        out = [header, sep]

        for r in rows:
            default_value = r["default_value"]
            choices = r["choices"]
            description = r["description"]
            if choices:
                description += f"<br> (choices: {choices})"
            if default_value:
                description += f"<br> (default value: {default_value})"

            out.append(
                f"| `{r['name']}` | {r['type']} | {r['required']} | {description} |"
            )
        return "\n".join(out)
