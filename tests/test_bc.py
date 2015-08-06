"""Backwards Compatibility Tests."""

from val import Optional, Schema, bc


def test_new_required_field():
    old_schema = Schema({'field1': str})
    new_schema = Schema({
        'field1': str,
        'field2': str})
    assert not bc.is_backward_compatible(new=new_schema, old=old_schema)


def test_identical_schemas():
    old_schema = Schema({'field1': str})
    new_schema = Schema({'field1': str})
    assert bc.is_backward_compatible(new=new_schema, old=old_schema)


def test_changed_type():
    old_schema = Schema({'field1': str})
    new_schema = Schema({'field1': int})
    assert not bc.is_backward_compatible(new=new_schema, old=old_schema)


def test_new_optional_field():
    old_schema = Schema({'field1': str})
    new_schema = Schema({
        'field1': str,
        Optional('field2'): str})
    assert bc.is_backward_compatible(new=new_schema, old=old_schema)


def test_required_field_removed():
    old_schema = Schema({'field1': str})
    new_schema = Schema({'field2': str})
    assert not bc.is_backward_compatible(new=new_schema, old=old_schema)


def test_required_to_optional():
    old_schema = Schema({'field1': str})
    new_schema = Schema({Optional('field1'): str})
    assert bc.is_backward_compatible(new=new_schema, old=old_schema)


def test_required_to_optional_of_incompatible_type():
    old_schema = Schema({'field1': str})
    new_schema = Schema({Optional('field1'): int})
    assert not bc.is_backward_compatible(new=new_schema, old=old_schema)


def test_change_to_incompatible_type():
    old_schema = Schema({'field1': str})
    new_schema = Schema({'field1': int})
    assert not bc.is_backward_compatible(new=new_schema, old=old_schema)


def test_change_to_more_general_type():
    old_schema = Schema({'field1': str})
    new_schema = Schema({'field1': object})
    assert bc.is_backward_compatible(new=new_schema, old=old_schema)


def test_change_from_instance_to_type():
    old_schema = Schema({'field1': 'foo'})
    new_schema = Schema({'field1': str})
    assert bc.is_backward_compatible(new=new_schema, old=old_schema)


def test_optional_to_required():
    old_schema = Schema({Optional('field1'): str})
    new_schema = Schema({'field1': str})
    assert not bc.is_backward_compatible(new=new_schema, old=old_schema)
