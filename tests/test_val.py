"""
Copyright (c) 2012-2013
Eric Casteleijn, <thisfred@gmail.com>
Vladimir Keleshev, <vladimir@keleshev.com>
"""

from tempfile import mkstemp
from val import NotValid, Optional, Or, And, Schema, Convert, Ordered
import pytest
from hotshot import Profile, stats


VAL_SCHEMA = {
    Optional('invisible'): bool,
    Optional('immutable'): bool,
    Optional('favorite_colors'): [str],
    Optional('favorite_foods'): [str],
    Optional('lucky_number'): int,
    Optional('shoe_size'): int,
    Optional('mother'): {
        Optional('name'): str,
        'nested': {'id': str}},
    Optional('father'): {
        Optional('name'): str,
        'nested': {'id': str}}}

VALID_TEST_DATA = {
    'invisible': False,
    'immutable': False,
    'favorite_colors': ['mauve', 'taupe', 'beige'],
    'favorite_foods': ['granola', 'shinola'],
    'lucky_number': 1,
    'shoe_size': 12,
    'mother': {
        'name': 'edna',
        'nested': {'id': '1232134'}},
    'father': {
        'nested': {'id': '9492921'}}}

INVALID_TEST_DATA = {
    'invisible': False,
    'immutable': 0,
    'favorite_colors': ['test', 'test2', None, 1233, 1.34, False],
    'favorite_foods': ['kraft cheese'],
    'lucky_number': 1,
    'shoe_size': 12,
    'mother': 'edna',
    'father': {
        'name': 'ed',
        'nested': {'id': '9492921'}}}


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
    assert (
        str(schema) ==
        "{<Optional: 'key2'>: <type 'str'>, 'key': <type 'str'>}")


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
    schema = Or(1, str, Convert(lambda x: int(x)))
    assert schema.validate(1) == 1
    assert schema.validate('foo') == 'foo'
    assert schema.validate('12') == '12'
    assert schema.validate(1.2231) == 1


def test_or_repr():
    schema = Or(1, str, Convert(lambda x: int(x)))
    assert str(schema).startswith(
        "<1 or <type 'str'> or <Convert: <function <lambda> at ")


def test_and():
    schema = And(str, Convert(lambda x: int(x)))
    assert schema.validate('12') == 12
    with pytest.raises(NotValid):
        schema.validate(12.1)
    with pytest.raises(NotValid):
        schema.validate('foo')
    with pytest.raises(NotValid):
        schema.validate('12.1')


def test_and_repr():
    schema = And(str, Convert(lambda x: int(x)))
    assert str(schema).startswith(
        "<<type 'str'> and <Convert: <function <lambda> at ")


def test_dont_care_values_in_dict():
    schema = Schema({
        'foo': int,
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
    assert str(schema) == "<Ordered: [<type 'str'>, <type 'int'>]>"


def test_callable_exception():
    schema = Schema(lambda x: x + 2)
    with pytest.raises(NotValid):
        schema.validate("foo")


def test_schema_parsing_profile():
    try:
        from schema import (
            Schema as SchemaSchema, Optional as SchemaOptional)
        from flatland import Dict, Boolean, List, String, Integer
    except ImportError:
        return

    SCHEMA_SCHEMA = {
        SchemaOptional('invisible'): bool,
        SchemaOptional('immutable'): bool,
        SchemaOptional('favorite_colors'): [str],
        SchemaOptional('favorite_foods'): [str],
        SchemaOptional('lucky_number'): int,
        SchemaOptional('shoe_size'): int,
        SchemaOptional('mother'): {
            SchemaOptional('name'): str,
            'nested': {'id': str}},
        SchemaOptional('father'): {
            SchemaOptional('name'): str,
            'nested': {'id': str}}}

    FlatlandSchema = Dict.of(
        Boolean.named('invisible').using(optional=True),
        Boolean.named('preserve').using(optional=True),
        List.named('favorite_colors').of(String).using(optional=True),
        List.named('favorite_foods').of(String).using(optional=True),
        Integer.named('lucky_number').using(optional=True),
        Integer.named('shoe_size').using(optional=True),
        Dict.named('mother').of(
            String.named('name').using(optional=True),
            Dict.named('nested').of(String.named('id'))),
        Dict.named('father').of(
            String.named('name').using(optional=True),
            Dict.named('nested').of(String.named('id')))).using(
                policy='duck')

    tmp_file, filename = mkstemp()
    profile = Profile(filename)
    print
    print "flatland"
    schema = FlatlandSchema()
    profile.start()
    schema.set(VALID_TEST_DATA)
    schema.validate()
    result = schema.value
    profile.stop()
    st = stats.load(filename)
    st.strip_dirs()
    st.sort_stats('time', 'calls')
    st.print_stats(20)
    assert result
    profile.close()
    print "schema"
    tmp_file, filename = mkstemp()
    profile = Profile(filename)
    schema = SchemaSchema(SCHEMA_SCHEMA)
    profile.start()
    result = schema.validate(VALID_TEST_DATA)
    profile.stop()
    st = stats.load(filename)
    st.strip_dirs()
    st.sort_stats('time', 'calls')
    st.print_stats(20)
    assert result
    profile.close()
    print "val"
    tmp_file, filename = mkstemp()
    profile = Profile(filename)
    schema = Schema(VAL_SCHEMA)
    profile.start()
    result = schema.validate(VALID_TEST_DATA)
    profile.stop()
    st = stats.load(filename)
    st.strip_dirs()
    st.sort_stats('time', 'calls')
    st.print_stats(20)
    profile.close()
    assert result


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


# Translated Schema tests
def test_and_schema():
    assert Schema(And(int, lambda n: 0 < n < 5)).validate(3) == 3
    with pytest.raises(NotValid):
        Schema(And(int, lambda n: 0 < n < 5)).validate(3.33)
    assert Schema(And(Convert(int), lambda n: 0 < n < 5)).validate(3.33) == 3
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
    assert (
        Schema(And([1, 0], lambda l: len(l) > 2)).validate([0, 1, 0]) ==
        [0, 1, 0])
    with pytest.raises(NotValid):
        Schema(And([1, 0], lambda l: len(l) > 2)).validate([0, 1])


def test_list_tuple_set_frozenset():
    assert Schema([int]).validate([1, 2]) == [1, 2]
    with pytest.raises(NotValid):
        Schema([int]).validate(['1', 2])
    assert Schema(set([int])).validate({1, 2}) == {1, 2}
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
    assert Schema({str: int}).validate({'a': 1, 'b': 2}) == {'a': 1, 'b': 2}
    with pytest.raises(NotValid):
        Schema({str: int}).validate({1: 1, 'b': 2})
    # XXX: I don't intend to support this. Keys are literal,
    # Optional(literal) or type.
    # self.assertEquals(
    #    Schema({Convert(str): Convert(int)}).validate({1: 3.14, 3.14: 1}),
    #    {'1': 3, '3.14': 1})


def test_dict_optional_keys():
    with pytest.raises(NotValid):
        Schema({Optional('a'): 1, 'b': 2}).validate({'a': 1})
    assert Schema({'a': 1, Optional('b'): 2}).validate({'a': 1}) == {'a': 1}
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
