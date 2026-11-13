"""Pydantic base for LLM reply items whose numbers may arrive as text ("30%", "1,234.5")."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


class LenientItem(BaseModel):
    """
    Purpose:
        Base for one item of an LLM JSON reply. Unknown keys are ignored, and every field typed
        `float` (or `float | None`) also accepts text: the first number in it is taken after
        thousands separators are removed ("30%" -> 30.0, "1,234.5万元" -> 1234.5, "约50" ->
        50.0); text with no number becomes None. Without this a model writing "30%" fails the
        whole reply.

    Contract:
        Input:
            the subclass's fields
        Output:
            pydantic model
        Raises:
            pydantic.ValidationError  -- wrong types other than numeric text, or numeric text
                                         without a number in a field that is not optional

    Used by:
        industry_graph.GuidanceItem  -- base
        industry_graph.ContractItem  -- base

    Test cases:
        TC-LI-001  "30%", "1,234.5万元", 12 and None parse; "不适用" becomes None; text fields
                   are left as text
    """

    model_config = ConfigDict(extra="ignore")

    @field_validator("*", mode="before")
    @classmethod
    def _parse_number(cls, value: Any, info: ValidationInfo) -> Any:
        if not isinstance(value, str) or info.field_name is None:
            return value
        annotation = cls.model_fields[info.field_name].annotation
        if float not in getattr(annotation, "__args__", (annotation,)):
            return value
        found = NUMBER.search(value.replace(",", ""))
        return float(found.group()) if found else None
