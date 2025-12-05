# mypy: disable-error-code=no-untyped-call
import importlib
import typing as t
from pathlib import Path

import mkdocs
from clios import Clios
from clios.core.main_parser import ParserAbc
from clios.core.operator_fn import OperatorFn
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure import StructureItem
from mkdocs.structure.files import File, Files
from mkdocs.structure.nav import Section
from mkdocs.structure.pages import Page


class CliosPluginConfig(mkdocs.config.base.Config):
    app = mkdocs.config.config_options.Type(str)


class CliosMkDocsPlugin(mkdocs.plugins.BasePlugin[CliosPluginConfig]):  # type: ignore
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
        return config

    def on_files(self, files: Files, *, config: MkDocsConfig) -> Files:
        """
        Called before MkDocs collects files.
        We generate .md files and let MkDocs see them as part of docs/.
        """
        self._generate_operator_docs(files, config)
        return files

        # ---------------------------------------------------------------

    def on_nav(self, nav, config: MkDocsConfig, files: Files):
        """Insert the Operator tree into navigation."""
        operator_pages: list[StructureItem] = []

        for item in self._items:
            file = files.get_file_from_path(f"operators/{item}.md")
            if file is None:
                continue
            operator_pages.append(Page(item, file, config))
        something = Section("Operators", operator_pages)
        nav.items.append(something)
        return nav

    # ------------------------------------------------------------------
    # Render markdown similar to print_detail()
    # ------------------------------------------------------------------
    def _generate_operator_docs(self, files: Files, config: MkDocsConfig) -> None:
        parser = self.app._parser
        operators = self.app._operators
        self._items: list[str] = []

        index_lines = []
        index_lines.append("# Operators")
        index_lines.append("")
        index_lines.append("| Name | Description |")
        index_lines.append("|------|-------------|")

        cache_dir = ".mkdocs_clios_cache"
        (Path(cache_dir) / "operators").mkdir(parents=True, exist_ok=True)
        for name, op_fn in operators.items():
            md = self._render_markdown_for_operator(name, op_fn, parser, index_lines)
            file_path = f"operators/{name}.md"
            path = Path(cache_dir) / file_path
            self._items.append(name)
            path.write_text(md, encoding="utf-8")
            print(f"[cli-docs] Generated {path}")  # noqa T201

            file = File(
                path=file_path,
                src_dir=cache_dir,
                dest_dir=config.site_dir,
                use_directory_urls=config.use_directory_urls,
            )
            files.append(file)

        file_path = "operators/index.md"
        index_path = Path(cache_dir) / file_path
        index_path.write_text("\n".join(index_lines), encoding="utf-8")
        self._items.insert(0, "index")
        file = File(
            path=file_path,
            src_dir=cache_dir,
            dest_dir=config.site_dir,
            use_directory_urls=config.use_directory_urls,
        )
        files.append(file)

    # ------------------------------------------------------------------
    def _render_markdown_for_operator(
        self, name: str, op_fn: OperatorFn, parser: ParserAbc, index_lines: list[str]
    ) -> str:
        synopsis, short, long, args_doc, kwds_doc = parser.get_details(
            name, op_fn, exe_name="xcdo"
        )

        # Build index -----------------------------------------------
        index_lines.append(f"| [{name}]({name}.md) | {short} |")

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
