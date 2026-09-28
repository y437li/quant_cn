"""Parse the mandatory contract docstring (CODING_STANDARD §3) into a typed record."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

SECTIONS = ("Purpose", "Contract", "Input", "Output", "Raises", "Used by", "Test cases")
_HEADING = re.compile(r"^\s*(Purpose|Contract|Input|Output|Raises|Used by|Test cases):\s*$")
_TC_ID = re.compile(r"\bTC-[A-Z]+-\d{3}\b")
_CALLER = re.compile(r"^([a-z_]+(?:\.[a-z_]+)*)\.([A-Z]\w*)(?:\.(\w+))?$")


@dataclass(frozen=True)
class UsedByEntry:
    """
    Purpose:
        One line of a `Used by:` section, split into the caller reference and its note.

    Contract:
        Input:
            text:   str         -- reference, e.g. "pipeline.LocalRunner.run" or "Makefile targets"
            note:   str         -- text after "--", may be empty
            cls:    str | None  -- class name when text is `package.Class[.method]`, else None
            method: str | None  -- method name when given, else None
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        core.docs.DocContract            -- `used_by` items
        core.docs.DocstringParser.parse  -- builds entries

    Test cases:
        TC-DSP-001  full contract docstring parses every section
    """

    text: str
    note: str = ""
    cls: str | None = None
    method: str | None = None


@dataclass(frozen=True)
class DocContract:
    """
    Purpose:
        The parsed contract of one class, method or module docstring.

    Contract:
        Input:
            sections:   frozenset[str]     -- section headings present (see SECTIONS)
            purpose:    str                -- Purpose text joined into one line; "" if absent
            used_by:    tuple[UsedByEntry] -- entries; empty for "(none yet)"
            test_cases: tuple[str]         -- TC IDs in the Test cases section, in order
            inputs, outputs, raises: str   -- Input / Output / Raises blocks, lines joined by "; "
            test_descriptions: dict[str, str]  -- TC ID -> its description text
        Output:
            frozen dataclass; `has`
        Raises:
            (none)

    Used by:
        core.docs.DocstringParser.parse  -- return type
        core.docs.CodeUnit               -- injected type or call

    Test cases:
        TC-DSP-001  full contract docstring parses every section
    """

    sections: frozenset[str] = frozenset()
    purpose: str = ""
    used_by: tuple[UsedByEntry, ...] = ()
    test_cases: tuple[str, ...] = field(default_factory=tuple)
    inputs: str = ""
    outputs: str = ""
    raises: str = ""
    test_descriptions: dict[str, str] = field(default_factory=dict)

    def has(self, *names: str) -> bool:
        """
        Purpose:
            True if every named section is present.

        Contract:
            Input:
                names: str  -- section headings, e.g. "Purpose", "Used by"
            Output:
                bool
            Raises:
                (none)
        """
        return all(n in self.sections for n in names)


class DocstringParser:
    """
    Purpose:
        Split a contract docstring into its sections: Purpose, Contract (Input, Output, Raises),
        Used by, Test cases.

    Contract:
        Input:
            (none)
        Output:
            instance; `parse(text) -> DocContract`
        Raises:
            (none)

    Used by:
        core.docs.ContractChecker   -- every class, method and module docstring
        core.docs.ContractLinter    -- injected type or call
        core.docs.CodeTableBuilder  -- injected type or call
        cli.QuantCnCli              -- injected type or call

    Test cases:
        TC-DSP-001  full contract docstring parses every section
        TC-DSP-002  "(none yet)" yields no Used by entries; non-class callers keep cls None
        TC-DSP-003  missing sections are absent; empty or None docstring gives an empty contract
        TC-DSP-004  TC IDs outside the Test cases section are ignored
        TC-DSP-005  Input/Output/Raises text and TC descriptions are kept
    """

    def parse(self, text: str | None) -> DocContract:
        """
        Purpose:
            Parse one docstring.

        Contract:
            Input:
                text: str | None  -- docstring as returned by ast.get_docstring
            Output:
                DocContract
            Raises:
                (none)
        """
        blocks = self._parse_sections(text or "")
        entries = tuple(
            self._parse_entry(line) for line in blocks.get("Used by", []) if line != "(none yet)"
        )
        case_lines = blocks.get("Test cases", [])
        cases = tuple(_TC_ID.findall("\n".join(case_lines)))
        return DocContract(
            sections=frozenset(blocks),
            purpose=" ".join(blocks.get("Purpose", [])),
            used_by=entries,
            test_cases=cases,
            inputs="; ".join(blocks.get("Input", [])),
            outputs="; ".join(blocks.get("Output", [])),
            raises="; ".join(blocks.get("Raises", [])),
            test_descriptions=self._parse_descriptions(case_lines),
        )

    def _parse_sections(self, text: str) -> dict[str, list[str]]:
        blocks: dict[str, list[str]] = {}
        current: str | None = None
        for raw in text.splitlines():
            heading = _HEADING.match(raw)
            if heading:
                current = heading.group(1)
                blocks.setdefault(current, [])
                continue
            line = raw.strip()
            if current and line:
                blocks[current].append(line)
        return blocks

    def _parse_descriptions(self, lines: list[str]) -> dict[str, str]:
        out: dict[str, str] = {}
        for line in lines:
            ids = _TC_ID.findall(line)
            if ids and line.startswith(ids[0]):
                out[ids[0]] = line[len(ids[0]) :].strip()
        return out

    def _parse_entry(self, line: str) -> UsedByEntry:
        ref, _, note = line.partition("--")
        ref = ref.strip()
        match = _CALLER.match(ref)
        if match:
            return UsedByEntry(ref, note.strip(), match.group(2), match.group(3))
        return UsedByEntry(ref, note.strip())
