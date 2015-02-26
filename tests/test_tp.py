"""Tests for integration with teleport."""

import json
import pytest
from pyrfc3339 import parse as rfc3339
from val import Schema, Optional, Or
from val.tp import (
    DeserializationError,
    SerializationError,
    document,
    to_val,
    from_val)


def test_teleport_struct():
    """A teleport Struct can be converted to an equivalent val schema."""
    todo = {
        "Struct": {
            "required": {"task": "String"},
            "optional": {
                "priority": "Integer",
                "deadline": "DateTime"}}}
    todo_val = to_val(todo)
    assert todo_val.validates({"task": "Return videotapes"})
    assert todo_val.validates({
        "task": "Return videotapes",
        "deadline": "2015-04-05T14:30:00Z"})
    assert not todo_val.validates({})
    assert not todo_val.validates({"task": 1})


def test_teleport_array():
    """A teleport Array can be converted to an equivalent val schema."""
    todo = {
        "Struct": {
            "required": {"tasks": {"Array": "String"}},
            "optional": {}}}
    todo_val = to_val(todo)
    assert todo_val.validates({"tasks": ["Return videotapes"]})
    assert todo_val.validates({"tasks": []})
    assert not todo_val.validates({"tasks": [1]})
    assert not todo_val.validates({"tasks": "Return videotapes"})


def test_serialize_to_teleport():
    """Appropriate val schemas can be serialized to teleport Struct schemas."""
    todo = Schema({
        "task": str,
        Optional("priority"): int,
        Optional("deadline"): rfc3339})
    assert from_val(todo) == {
        "Struct": {
            "required": {"task": "String"},
            "optional": {
                "priority": "Integer",
                "deadline": "DateTime"}}}


def test_serialize_array():
    """Appropriate val schemas can be serialized to teleport Array schemas."""
    todo = Schema({"tasks": [str]})
    assert from_val(todo) == {
        "Struct": {
            "required": {"tasks": {"Array": "String"}},
            "optional": {}}}


def test_serialize_map():
    """Appropriate val schemas can be serialized to teleport Map schemas."""
    todo = Schema({str: int})
    assert from_val(todo) == {"Map": "Integer"}


def test_serialize_unserializables():
    """Val schemas that cannot be serialized raise appropriate exceptions."""
    todo = Schema({"task": Or(str, int)})
    with pytest.raises(SerializationError):
        from_val(todo)


EXPECTED = """{
  "Struct": {
    "optional": {
      "priority": "Integer",
      "status": "String"
    },
    "required": {
      "task": "String"
    }
  }
}
"""


def test_document():
    """Val schemas can be documented as teleport schemas."""
    todo = Schema({
        "task": str,
        Optional("priority"): int,
        Optional("status"): str})
    output = document(todo)
    expected = {
        "Struct": {
            "optional": {
                "priority": "Integer",
                "status": "String"},
            "required": {"task": "String"}}}
    # json.loads because the json.dumps in python2 and 3 are subtly different.
    assert json.loads(output) == expected


INTEGERS = {-1, 0, 1, 3123342342349238429834}
DECIMALS = {-1.0, 1.0, 1.1, 1e4}
BOOLEANS = {True, False}
STRINGS = {u"", u"2007-04-05T14:30:00Z", u"Boolean"}
DATETIMES = {u"2007-04-05T14:30:00Z"}
ALL = INTEGERS | DECIMALS | BOOLEANS | STRINGS | DATETIMES

SCHEMA_VALID_NOT_VALID = (
    ("Integer", INTEGERS, ALL - INTEGERS),
    ("Decimal", DECIMALS, ALL - (DECIMALS | INTEGERS)),
    ("Boolean", BOOLEANS, ALL - BOOLEANS),
    ("String", STRINGS, ALL - STRINGS),
    ("JSON", ALL, ({1, 2}, object())),
    ("DateTime", DATETIMES, ALL - DATETIMES),
    ({"Array": "Integer"}, [[], [1], [2, 3]], ALL),
    ({"Map": "Integer"}, [{}, {"a": 1}, {"a": 123, "b": -123}], ALL),
    ({"Struct": {
        "required": {"a": "Integer"},
        "optional": {"b": "Integer"}}},
     [{"a": 1}, {"a": -1, "b": 13}],
     list(ALL) + [{"a": 1.0}]),
    ("Schema",
     (u"Integer",
      u"Decimal",
      u"Boolean",
      u"String",
      u"JSON",
      u"DateTime",
      u"Schema",
      {"Array": "String"},
      {"Map": "String"},
      {"Struct": {
          "required": {},
          "optional": {},
          "doc.order": []}}),
     ALL - {u"Boolean"}))


@pytest.mark.parametrize("schema,valid,not_valid", SCHEMA_VALID_NOT_VALID)
def test_to_val(schema, valid, not_valid):
    """Converted teleport schemas validate correctly."""
    val_schema = to_val(schema)
    for value in valid:
        assert val_schema.validates(value)
    for value in not_valid:
        assert not val_schema.validates(value)


@pytest.mark.parametrize("schema", [s[0] for s in SCHEMA_VALID_NOT_VALID])
def test_round_trip(schema):
    """Round tripping teleport schemas does not change them."""
    assert from_val(to_val(schema)) == schema


@pytest.mark.parametrize("schema", (
    "Wat",
    {"foo": "wat"},
    {"Struct": {}},
    {"Struct": {"optional": {}}},
    {"Struct": {"required": {}}},
    {"Struct": {
        "required": {},
        "optional": 12}},
    {"Struct": {
        "required": "foo",
        "optional": {}}},
    {"Struct": {
        "required": {"a": "Wat"},
        "optional": {}}},
    {"Struct": {
        "required": {},
        "optional": {"a": "Wat"}}},
    {"Map": "Wat"},
    {"Map": 4},
    {"Array": "Wat"},
    {"Array": 4},
))
def test_detects_broken_schemas(schema):
    """Invalid teleport schemas raise appropriate exceptions."""
    with pytest.raises(DeserializationError):
        to_val(schema)
