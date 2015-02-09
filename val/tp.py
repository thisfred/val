"""Convert teleport schemas into val schemas and vice versa."""

import json
from decimal import Decimal
from val import BaseSchema, Optional, Or, Schema
from sys import version_info
from strict_rfc3339 import validate_rfc3339


PYTHON_VERSION = version_info[0]
INTEGER = int if PYTHON_VERSION == 3 else Or(int, long)  # noqa
STRING = str if PYTHON_VERSION == 3 else Or(str, unicode)  # noqa
TeleportDecimal = Or(float, Decimal, int)


def is_jsonable(value):
    """Detect if the value can be converted to JSON."""
    try:
        json.dumps(value)
    except TypeError:
        return False

    return True


def is_valid_teleport(value):
    """Detect if the value is a valid teleport schema."""
    try:
        _translate(value)
    except DeserializationError:
        return False

    return True


# XXX: this is pretty icky and error prone. (for instance schemas that use
# their own logically equivalent definitions won't be exportable this way.)
VAL_PRIMITIVES = {
    Decimal: "Decimal",
    INTEGER: "Integer",
    STRING: "String",
    TeleportDecimal: "Decimal",
    bool: "Boolean",
    float: "Decimal",
    int: "Integer",
    is_jsonable: "JSON",
    is_valid_teleport: "Schema",
    str: "String",
    validate_rfc3339: "DateTime",
}


class SerializationError(Exception):

    """Value cannot be serialized."""

    pass


class DeserializationError(Exception):

    """Value cannot be deserialized."""

    pass


PRIMITIVES = {
    'Integer': INTEGER,
    'Decimal': TeleportDecimal,
    'Boolean': bool,
    'String': STRING,
    'JSON': is_jsonable,
    'DateTime': validate_rfc3339,
    'Schema': is_valid_teleport}


def _translate_struct(inner_dict):
    """Translate a teleport Struct into a val subschema."""
    try:
        optional = inner_dict['optional'].items()
        required = inner_dict['required'].items()
    except KeyError as ex:
        raise DeserializationError("Missing key: {}".format(ex))
    except AttributeError as ex:
        raise DeserializationError(
            "Invalid Structure: {}".format(inner_dict))

    val_dict = {k: _translate(v) for k, v in required}
    val_dict.update({Optional(k): _translate(v) for k, v in optional})
    return val_dict


COMPOSITES = {
    "Array": lambda value: [_translate(value)],
    "Map": lambda value: {str: _translate(value)},
    "Struct": _translate_struct}


def _translate_composite(teleport_value):
    """Translate a composite teleport value into a val subschema."""
    for key in ("Array", "Map", "Struct"):
        value = teleport_value.get(key)
        if value is None:
            continue
        return COMPOSITES[key](value)

    raise DeserializationError(
        "Could not interpret %r as a teleport schema." % teleport_value)


def _translate(teleport_value):
    """Translate a teleport value in to a val subschema."""
    if isinstance(teleport_value, dict):
        return _translate_composite(teleport_value)

    if teleport_value in PRIMITIVES:
        return PRIMITIVES[teleport_value]

    raise DeserializationError(
        "Could not interpret %r as a teleport schema." % teleport_value)


def to_val(teleport_schema):
    """Convert a parsed teleport schema to a val schema."""
    translated = _translate(teleport_schema)
    if isinstance(translated, BaseSchema):
        return translated

    return Schema(translated)


def _dict_to_teleport(dict_value):
    """Convert a val schema dictionary to teleport."""
    if len(dict_value) == 1:
        for key, value in dict_value.items():
            if key is str:
                return {"Map": from_val(value)}

    optional = {}
    required = {}
    for key, value in dict_value.items():
        if isinstance(key, Optional):
            optional[key.value] = from_val(value)
        else:
            required[key] = from_val(value)

    return {"Struct": {
        "required": required,
        "optional": optional}}


def from_val(val_schema):
    """Serialize a val schema to teleport."""
    definition = getattr(val_schema, "definition", val_schema) if isinstance(
        val_schema, BaseSchema) else val_schema
    if isinstance(definition, dict):
        return _dict_to_teleport(definition)

    if isinstance(definition, list):
        # teleport only supports a single type by default
        if len(definition) == 1:
            return {"Array": from_val(definition[0])}

    if definition in VAL_PRIMITIVES:
        return VAL_PRIMITIVES[definition]

    raise SerializationError(
        "Serializing %r not (yet) supported." % definition)


def document(schema):
    """Print a documented teleport version of the schema."""
    teleport_schema = from_val(schema)
    return json.dumps(teleport_schema, sort_keys=True, indent=2)
