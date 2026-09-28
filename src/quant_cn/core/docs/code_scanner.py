"""AST view of Python modules: classes, methods, module functions, names each class references."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class MethodInfo:
    """
    Purpose:
        One function defined directly in a class body.

    Contract:
        Input:
            name, lineno, end_lineno  -- as in the AST (1-based, inclusive)
            docstring:   str | None
            is_property: bool  -- decorated with @property
            is_abstract: bool  -- decorated with @abstractmethod
            decorators:  tuple[str, ...]  -- unparsed decorator expressions
        Output:
            frozen dataclass; `n_lines`, `is_public`
        Raises:
            (none)

    Used by:
        core.docs.ClassInfo                -- `methods`
        core.docs.CodeScanner.read_module  -- builds records
        core.docs.ModuleInfo               -- injected type or call

    Test cases:
        TC-CS-001  classes, methods and module functions are listed with line spans
    """

    name: str
    lineno: int
    end_lineno: int
    docstring: str | None = None
    is_property: bool = False
    is_abstract: bool = False
    decorators: tuple[str, ...] = ()

    @property
    def n_lines(self) -> int:
        """
        Purpose:
            Physical lines including docstring and blanks.

        Contract:
            Input:
                (none)
            Output:
                int >= 1
            Raises:
                (none)
        """
        return self.end_lineno - self.lineno + 1

    @property
    def is_public(self) -> bool:
        """
        Purpose:
            True for names without a leading underscore.

        Contract:
            Input:
                (none)
            Output:
                bool
            Raises:
                (none)
        """
        return not self.name.startswith("_")


@dataclass(frozen=True)
class ClassInfo:
    """
    Purpose:
        One top-level class: span, bases, docstring, methods and the names its body references.

    Contract:
        Input:
            name, lineno, end_lineno, docstring
            bases:      tuple[str, ...]  -- unparsed base expressions
            methods:    tuple[MethodInfo, ...]
            references: frozenset[str]   -- identifiers used in the body (names and attribute roots)
        Output:
            frozen dataclass; `n_lines`, `list_public_methods`
        Raises:
            (none)

    Used by:
        core.docs.ModuleInfo               -- `classes`
        core.docs.CodeScanner.read_module  -- builds records
        core.docs.NameChecker              -- method names, module-class match
        core.docs.CodeUnit                 -- injected type or call

    Test cases:
        TC-CS-001  classes, methods and module functions are listed with line spans
        TC-CS-002  references include annotations, bases and call targets but not docstrings
    """

    name: str
    lineno: int
    end_lineno: int
    docstring: str | None
    bases: tuple[str, ...]
    methods: tuple[MethodInfo, ...]
    references: frozenset[str]

    @property
    def n_lines(self) -> int:
        """
        Purpose:
            Physical lines of the class.

        Contract:
            Input:
                (none)
            Output:
                int >= 1
            Raises:
                (none)
        """
        return self.end_lineno - self.lineno + 1

    def list_public_methods(self) -> list[MethodInfo]:
        """
        Purpose:
            Methods and properties without a leading underscore, in source order.

        Contract:
            Input:
                (none)
            Output:
                list[MethodInfo]
            Raises:
                (none)
        """
        return [m for m in self.methods if m.is_public]


@dataclass(frozen=True)
class ModuleInfo:
    """
    Purpose:
        One scanned Python file.

    Contract:
        Input:
            path:       Path  -- file path
            module:     str   -- dotted name relative to the scan root ("quant_cn.lake.fetch_log")
            n_lines:    int   -- physical lines
            docstring:  str | None
            classes:    tuple[ClassInfo, ...]
            functions:  tuple[MethodInfo, ...]  -- module-level functions
            constants:  tuple[str, ...]         -- module-level UPPER_SNAKE names
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        core.docs.CodeScanner.read_module  -- return type
        core.docs.ContractChecker          -- whole-tree checks
        core.docs.NameChecker              -- file and method names
        core.docs.CodeUnit                 -- injected type or call

    Test cases:
        TC-CS-001  classes, methods and module functions are listed with line spans
    """

    path: Path
    module: str
    n_lines: int
    docstring: str | None
    classes: tuple[ClassInfo, ...] = ()
    functions: tuple[MethodInfo, ...] = ()
    constants: tuple[str, ...] = field(default_factory=tuple)


class CodeScanner:
    """
    Purpose:
        Parse Python files with `ast` into ModuleInfo records (no import, no execution).

    Contract:
        Input:
            (none)
        Output:
            instance; `read_module(path, root) -> ModuleInfo`
        Raises:
            (none at construction)

    Used by:
        core.docs.ContractChecker  -- scans src/ and scripts/
        core.docs.IndexChecker     -- scans .py files listed in indexes
        core.docs.SizeChecker      -- scans src/, tests/, scripts/
        core.docs.NameChecker      -- scans src/, tests/, scripts/
        core.docs.ContractLinter   -- injected type or call

    Test cases:
        TC-CS-001  classes, methods and module functions are listed with line spans
        TC-CS-002  references include annotations, bases and call targets but not docstrings
        TC-CS-003  a syntax error raises SyntaxError with the file name
    """

    def read_module(self, path: Path, root: Path) -> ModuleInfo:
        """
        Purpose:
            Scan one file.

        Contract:
            Input:
                path: Path  -- a .py file
                root: Path  -- directory the dotted module name is relative to (e.g. src/)
            Output:
                ModuleInfo
            Raises:
                SyntaxError  -- the file does not parse
                OSError      -- unreadable file
        """
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        rel = path.relative_to(root).with_suffix("")
        module = ".".join(p for p in rel.parts if p != "__init__")
        classes = tuple(self._build_class(n) for n in tree.body if isinstance(n, ast.ClassDef))
        functions = tuple(
            self._build_method(n)
            for n in tree.body
            if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)
        )
        return ModuleInfo(
            path=path,
            module=module,
            n_lines=len(text.splitlines()),
            docstring=ast.get_docstring(tree),
            classes=classes,
            functions=functions,
            constants=self._list_constants(tree),
        )

    def _build_class(self, node: ast.ClassDef) -> ClassInfo:
        methods = tuple(
            self._build_method(n)
            for n in node.body
            if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)
        )
        return ClassInfo(
            name=node.name,
            lineno=node.lineno,
            end_lineno=node.end_lineno or node.lineno,
            docstring=ast.get_docstring(node),
            bases=tuple(ast.unparse(b) for b in node.bases),
            methods=methods,
            references=frozenset(self._list_references(node)),
        )

    def _build_method(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> MethodInfo:
        decorators = tuple(ast.unparse(d) for d in node.decorator_list)
        return MethodInfo(
            name=node.name,
            lineno=node.lineno,
            end_lineno=node.end_lineno or node.lineno,
            docstring=ast.get_docstring(node),
            is_property="property" in decorators,
            is_abstract="abstractmethod" in decorators,
            decorators=decorators,
        )

    def _list_references(self, node: ast.ClassDef) -> set[str]:
        names = {ast.unparse(b).split(".")[-1] for b in node.bases}
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                names.add(child.id)
            elif isinstance(child, ast.Attribute):
                names.add(child.attr)
        names.discard(node.name)
        return names

    def _list_constants(self, tree: ast.Module) -> tuple[str, ...]:
        out: list[str] = []
        for node in tree.body:
            targets = node.targets if isinstance(node, ast.Assign) else []
            if isinstance(node, ast.AnnAssign):
                targets = [node.target]
            out += [t.id for t in targets if isinstance(t, ast.Name) and t.id.isupper()]
        return tuple(out)
