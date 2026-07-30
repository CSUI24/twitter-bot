"""Runtime patches for the generated `twitter_openapi_python_generated` models.

The OpenAPI spec these models are generated from declares collection fields as
required arrays, but X frequently sends `null` for an empty collection. Pydantic then
rejects a response for a request that already succeeded — e.g. a tweet is posted, yet
`create_tweet` raises `4 validation errors for Entities`.

Treating `null` as an empty list keeps the generated types intact while accepting what
X actually sends.
"""

import inspect
import typing

import twitter_openapi_python_generated.models as models
from pydantic import BaseModel, BeforeValidator

_patched = False


def _null_to_empty_list(value: object) -> object:
    return [] if value is None else value


def relax_null_lists() -> None:
    """Make every required list field on the generated models accept `null`.

    Idempotent; safe to call on every client build.
    """
    global _patched
    if _patched:
        return

    for model in vars(models).values():
        if not (inspect.isclass(model) and issubclass(model, BaseModel)):
            continue

        relaxed = False
        for field in model.model_fields.values():
            if field.is_required() and typing.get_origin(field.annotation) is list:
                field.metadata.append(BeforeValidator(_null_to_empty_list))
                relaxed = True

        if relaxed:
            model.model_rebuild(force=True)

    _patched = True
