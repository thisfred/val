"""
Tests for val.

Copyright (c) 2012-2014
Eric Casteleijn, <thisfred@gmail.com>
Vladimir Keleshev, <vladimir@keleshev.com>
"""

import doctest
from val import NotValid, Optional, Or, And, Schema, Convert, Ordered
import pytest


def test_identity():
    schema = Schema('test')
    assert schema.validate('test') == 'test'


def test_non_identity():
    schema = Schema('test')
    with pytest.raises(NotValid):
        schema.validate('bar')


def test_type_check():
    schema = Schema(str)
    assert schema.validate('test') == 'test'


def test_failing_type_check():
    schema = Schema(int)
    with pytest.raises(NotValid):
        schema.validate('test')


def test_dictionary():
    schema = Schema({'key': str})
    assert schema.validate({'key': 'val'}) == {'key': 'val'}


def test_dictionary_not_a_dict():
    schema = Schema({'key': str})
    with pytest.raises(NotValid):
        schema.validate('foo')


def test_dictionary_optional():
    schema = Schema({'key': str, Optional('key2'): str})
    assert schema.validate({'key': 'val'}) == {'key': 'val'}


def test_dictionary_optional_repr():
    schema = Schema({'key': str, Optional('key2'): str})
    assert "<Optional: 'key2'>: <class 'str'>" in str(schema)
    assert "'key': <class 'str'>" in str(schema)


def test_dictionary_optional_missing():
    schema = Schema({'key': str, Optional('key2', default='val2'): str})
    assert schema.validate(
        {'key': 'val'}) == {'key': 'val', 'key2': 'val2'}


def test_regression_validating_twice_works():
    schema = Schema({
        'key': str,
        Optional('key2', default='val2', null_values=(None,)): Or(
            str, None)})
    assert (
        schema.validate({'key': 'val', 'key2': 'other_val'}) ==
        {'key': 'val', 'key2': 'other_val'})
    assert schema.validate(
        {'key': 'new_val'}) == {'key': 'new_val', 'key2': 'val2'}


def test_dictionary_optional_null_value():
    schema = Schema({
        'key': str,
        Optional('key2', default='val2', null_values=(None,)): Or(
            str, None)})
    assert (
        schema.validate({'key': 'val', 'key2': None}) ==
        {'key': 'val', 'key2': 'val2'})


def test_dictionary_optional_not_missing():
    schema = Schema({'key': str, Optional(
        'key2', default='val2'): Or(str, None)})
    assert schema.validate({
        'key': 'val',
        'key2': None}) == {'key': 'val', 'key2': None}


def test_dictionary_wrong_key():
    schema = Schema({'key': str})
    with pytest.raises(NotValid):
        schema.validate({'not_key': 'val'})


def test_dictionary_missing_key():
    schema = Schema({'key': str, 'key2': str})
    with pytest.raises(NotValid):
        schema.validate({'key': 'val'})


def test_dictionary_leftover_key():
    schema = Schema({'key': str})
    with pytest.raises(NotValid):
        schema.validate({'key': 'val', 'key2': 'val2'})


def test_list_data():
    schema = Schema([str])
    assert schema.validates(['1', '2', '3'])


def test_list_data_wrong_type():
    schema = Schema([str])
    assert not schema.validates(['1', '2', 3])


def test_list_data_multiple_types():
    schema = Schema([str, int])
    assert schema.validates(['1', '2', 3])


def test_not_list():
    schema = Schema(['1', '2', '3'])
    assert not schema.validates('1')


def test_list_not_found():
    schema = Schema(['1', '2', '3'])
    assert not schema.validates('12')


def test_or():
    schema = Or(1, str, Convert(int))
    assert schema.validate(1) == 1
    assert schema.validate('foo') == 'foo'
    assert schema.validate('12') == '12'
    assert schema.validate(1.2231) == 1


def test_or_repr():
    schema = Or(1, str, Convert(int))
    assert str(schema).startswith(
        "<1 or <class 'str'> or <Convert: <class ")


def test_and():
    schema = And(str, Convert(int))
    assert schema.validate('12') == 12
    with pytest.raises(NotValid):
        schema.validate(12.1)
    with pytest.raises(NotValid):
        schema.validate('foo')
    with pytest.raises(NotValid):
        schema.validate('12.1')


def test_and_repr():
    schema = And(str, Convert(int))
    assert str(schema).startswith(
        "<<class 'str'> and <Convert: <class ")


def test_dont_care_values_in_dict():
    schema = Schema(
        {'foo': int,
            'bar': str,
            str: object})
    assert (
        schema.validate({
            'foo': 12,
            'bar': 'bar',
            'qux': 'baz',
            'fnord': [1, 2, 'donkey kong']}) ==
        {
            'foo': 12,
            'bar': 'bar',
            'qux': 'baz',
            'fnord': [1, 2, 'donkey kong']})


def test_callable():
    schema = Schema(lambda x: x < 2)
    assert schema.validate(1) == 1


def test_callable_gives_readable_error():

    def less_than_two(value):
        """Must be less than two."""
        return value < 2

    schema = Schema(less_than_two)
    with pytest.raises(NotValid) as ctx:
        schema.validate(12)
    assert ctx.value.args == (
        "12 not validated by 'Must be less than two.'",)


def test_callable_gives_sensible_error():

    def less_than_two(value):
        return value < 2

    schema = Schema(less_than_two)
    with pytest.raises(NotValid) as ctx:
        schema.validate(12)
    assert ctx.value.args == ("12 not validated by 'less_than_two'",)


def test_convert():
    schema = Convert(lambda x: x + 2)
    assert schema.validate(1) == 3


def test_ordered():
    schema = Ordered([str, int])
    assert schema.validates(['1', 3])
    assert not schema.validates([1, '3'])
    assert not schema.validates(['1', 3, 4])
    assert not schema.validates(['1'])


def test_ordered_repr():
    schema = Ordered([str, int])
    assert str(schema) == "<Ordered: [<class 'str'>, <class 'int'>]>"


def test_callable_exception():
    schema = Schema(lambda x: x + 2)
    with pytest.raises(NotValid):
        schema.validate("foo")


def test_subschemas():
    schema1 = Schema({'foo': str, str: int})
    schema2 = Schema(
        {'key1': schema1,
            'key2': schema1,
            str: schema1})
    assert schema2.validates(
        {'key1': {'foo': 'bar'},
            'key2': {'foo': 'qux', 'baz': 43},
            'whatever': {'foo': 'doo', 'fsck': 22, 'tsk': 2992}})
    assert not schema2.validates(
        {'key1': {'doo': 'bar'},
            'key2': {'foo': 'qux', 'baz': 43},
            'whatever': {'foo': 'doo', 'fsck': 22, 'tsk': 2992}})
    assert not schema2.validates(
        {'key1': {'doo': 'bar'},
            'key2': {'foo': 'qux', 12: 43},
            'whatever': {'foo': 'doo', 'fsck': 22, 'tsk': 2992}})
    assert not schema2.validates(
        {'key1': {'foo': 'bar'},
            'key2': {'foo': 'qux', 'baz': 'derp'},
            'whatever': {'foo': 'doo', 'fsck': 22, 'tsk': 2992}})
    assert not schema2.validates(
        {'key1': {'foo': 'bar'},
            'key2': {'foo': 'qux', 'baz': 'derp'},
            12: {'foo': 'doo', 'fsck': 22, 'tsk': 2992}})
    assert not schema2.validates(
        {'key1': {'foo': 'bar'},
            'key2': {'foo': 'qux', 'baz': 'derp'},
            'whatever': {}})


def test_and_schema():
    assert Schema(And(int, lambda n: 0 < n < 5)).validate(3) == 3
    with pytest.raises(NotValid):
        Schema(And(int, lambda n: 0 < n < 5)).validate(3.33)
    assert Schema(
        And(Convert(int), lambda n: 0 < n < 5)).validate(3.33) == 3
    with pytest.raises(NotValid):
        Schema(And(Convert(int), lambda n: 0 < n < 5)).validate('3.33')


def test_or_schema():
    assert Schema(Or(int, dict)).validate(5) == 5
    assert Schema(Or(int, dict)).validate({}) == {}
    with pytest.raises(NotValid):
        Schema(Or(int, dict)).validate('hai')
    assert Schema(Or(int)).validate(4) == 4
    with pytest.raises(NotValid):
        Schema(Or()).validate(2)


def test_validate_list():
    assert Schema([1, 0]).validate([1, 0, 1, 1]) == [1, 0, 1, 1]
    assert Schema([1, 0]).validate([]) == []
    with pytest.raises(NotValid):
        Schema([1, 0]).validate(0)
    with pytest.raises(NotValid):
        Schema([1, 0]).validate([2])
    assert Schema(
        And([1, 0], lambda l: len(l) > 2)).validate([0, 1, 0]) == [0, 1, 0]
    with pytest.raises(NotValid):
        Schema(And([1, 0], lambda l: len(l) > 2)).validate([0, 1])


def test_list_tuple_set_frozenset():
    assert Schema([int]).validate([1, 2]) == [1, 2]
    with pytest.raises(NotValid):
        Schema([int]).validate(['1', 2])
    assert Schema(set([int])).validate(set([1, 2])) == set([1, 2])
    with pytest.raises(NotValid):
        Schema(set([int])).validate([1, 2])
    with pytest.raises(NotValid):
        Schema(set([int])).validate(['1', 2])
    assert Schema(tuple([int])).validate(tuple([1, 2])) == tuple([1, 2])
    with pytest.raises(NotValid):
        Schema(tuple([int])).validate([1, 2])


def test_strictly():
    assert Schema(int).validate(1) == 1
    with pytest.raises(NotValid):
        Schema(int).validate('1')


def test_dict():
    assert Schema({'key': 5}).validate({'key': 5}) == {'key': 5}
    with pytest.raises(NotValid):
        Schema({'key': 5}).validate({'key': 'x'})
    assert Schema({'key': int}).validate({'key': 5}) == {'key': 5}
    assert (
        Schema({'n': int, 'f': float}).validate({'n': 5, 'f': 3.14}) ==
        {'n': 5, 'f': 3.14})
    with pytest.raises(NotValid):
        Schema({'n': int, 'f': float}).validate({'n': 3.14, 'f': 5})
    with pytest.raises(NotValid):
        Schema({'key': 5}).validate({})
    with pytest.raises(NotValid):
        Schema({'key': 5}).validate({'n': 5})
    with pytest.raises(NotValid):
        Schema({}).validate({'n': 5})


def test_dict_keys():
    assert Schema(
        {str: int}).validate({'a': 1, 'b': 2}) == {'a': 1, 'b': 2}
    with pytest.raises(NotValid):
        Schema({str: int}).validate({1: 1, 'b': 2})
    # XXX: I don't intend to support this. Keys are literal,
    # Optional(literal) or type.
    # self.assertEqual(
    #    Schema({Convert(str): Convert(int)}).validate({1: 3.14, 3.14: 1}),
    #    {'1': 3, '3.14': 1})


def test_dict_optional_keys():
    with pytest.raises(NotValid):
        Schema({Optional('a'): 1, 'b': 2}).validate({'a': 1})
    assert Schema(
        {'a': 1, Optional('b'): 2}).validate({'a': 1}) == {'a': 1}
    assert (
        Schema({'a': 1, Optional('b'): 2}).validate({'a': 1, 'b': 2}) ==
        {'a': 1, 'b': 2})
    with pytest.raises(NotValid):
        Schema({Optional('a'): 1}).validate({'a': 2})


def test_validate_object():
    schema = Schema({object: str})
    assert schema.validate({42: 'str'}) == {42: 'str'}
    with pytest.raises(NotValid):
        schema.validate({42: 777})


def test_issue_9_prioritized_key_comparison():
    schema = Schema({'key': 42, object: 42})
    assert schema.validate({'key': 42, 777: 42}) == {'key': 42, 777: 42}


def test_issue_9_prioritized_key_comparison_in_dicts():
    # http://stackoverflow.com/questions/14588098/docopt-schema-validation
    schema = Schema(
        {'ID': Convert(int),  # , error='ID should be an int'),
            'FILE': Or(None, Convert(open)),  # , error='FILE not opened')),
            str: object})  # all type keys are optional
    data = {'ID': 10, 'FILE': None, 'other': 'other', 'other2': 'other2'}
    assert schema.validate(data) == data
    data = {'ID': 10, 'FILE': None}
    assert schema.validate(data) == data


def test_schema_with_additional_validators():

    def total_greater_than_12(value):
        """foo + bar > 12."""
        return value['foo'] + value['bar'] > 12

    schema = Schema({
        'foo': int,
        'bar': int},
        additional_validators=(total_greater_than_12,))

    assert schema.validates({'foo': 7, 'bar': 7})
    with pytest.raises(NotValid) as ctx:
        schema.validate({'foo': 5, 'bar': 7})
    assert ctx.value.args[0].endswith(
        "not validated by additional validator 'foo + bar > 12.'")


def test_documentation():
    result = doctest.testfile("README.rst")
    assert result.failed == 0
