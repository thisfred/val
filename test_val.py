"""
Tests for val.

Copyright (c) 2012-2014
Eric Casteleijn, <thisfred@gmail.com>
Vladimir Keleshev, <vladimir@keleshev.com>
"""

import doctest
from val import NotValid, Optional, Or, And, Schema, Convert, Ordered
from unittest import TestCase


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


class TestVal(TestCase):

    def test_identity(self):
        schema = Schema('test')
        self.assertEqual(schema.validate('test'), 'test')

    def test_non_identity(self):
        schema = Schema('test')
        self.assertRaises(NotValid, schema.validate, 'bar')

    def test_type_check(self):
        schema = Schema(str)
        self.assertEqual(schema.validate('test'), 'test')

    def test_failing_type_check(self):
        schema = Schema(int)
        self.assertRaises(NotValid, schema.validate, 'test')

    def test_dictionary(self):
        schema = Schema({'key': str})
        self.assertEqual(schema.validate({'key': 'val'}), {'key': 'val'})

    def test_dictionary_not_a_dict(self):
        schema = Schema({'key': str})
        self.assertRaises(NotValid, schema.validate, 'foo')

    def test_dictionary_optional(self):
        schema = Schema({'key': str, Optional('key2'): str})
        self.assertEqual(schema.validate({'key': 'val'}), {'key': 'val'})

    def test_dictionary_optional_repr(self):
        schema = Schema({'key': str, Optional('key2'): str})
        self.assertIn("<Optional: 'key2'>: <class 'str'>", str(schema))
        self.assertIn("'key': <class 'str'>", str(schema))

    def test_dictionary_optional_missing(self):
        schema = Schema({'key': str, Optional('key2', default='val2'): str})
        self.assertEqual(
            schema.validate({'key': 'val'}),
            {'key': 'val',
             'key2': 'val2'})

    def test_regression_validating_twice_works(self):
        schema = Schema({
            'key': str,
            Optional('key2', default='val2', null_values=(None,)): Or(
                str, None)})
        self.assertEqual(
            schema.validate({'key': 'val', 'key2': 'other_val'}),
            {'key': 'val',
             'key2': 'other_val'})
        self.assertEqual(
            schema.validate({'key': 'new_val'}),
            {'key': 'new_val',
             'key2': 'val2'})

    def test_dictionary_optional_null_value(self):
        schema = Schema({
            'key': str,
            Optional('key2', default='val2', null_values=(None,)): Or(
                str, None)})
        self.assertEqual(
            schema.validate({
                'key': 'val',
                'key2': None}),
            {'key': 'val',
             'key2': 'val2'})

    def test_dictionary_optional_not_missing(self):
        schema = Schema({'key': str, Optional(
            'key2', default='val2'): Or(str, None)})
        self.assertEqual(
            schema.validate({
                'key': 'val',
                'key2': None}),
            {'key': 'val',
             'key2': None})

    def test_dictionary_wrong_key(self):
        schema = Schema({'key': str})
        self.assertRaises(NotValid, schema.validate, {'not_key': 'val'})

    def test_dictionary_missing_key(self):
        schema = Schema({'key': str, 'key2': str})
        self.assertRaises(NotValid, schema.validate, {'key': 'val'})

    def test_dictionary_leftover_key(self):
        schema = Schema({'key': str})
        self.assertRaises(
            NotValid, schema.validate, {'key': 'val', 'key2': 'val2'})

    def test_list_data(self):
        schema = Schema([str])
        self.assertTrue(schema.validates(['1', '2', '3']))

    def test_list_data_wrong_type(self):
        schema = Schema([str])
        self.assertFalse(schema.validates(['1', '2', 3]))

    def test_list_data_multiple_types(self):
        schema = Schema([str, int])
        self.assertTrue(schema.validates(['1', '2', 3]))

    def test_not_list(self):
        schema = Schema(['1', '2', '3'])
        self.assertFalse(schema.validates('1'))

    def test_list_not_found(self):
        schema = Schema(['1', '2', '3'])
        self.assertFalse(schema.validates('12'))

    def test_or(self):
        schema = Or(1, str, Convert(lambda x: int(x)))
        self.assertEqual(schema.validate(1), 1)
        self.assertEqual(schema.validate('foo'), 'foo')
        self.assertEqual(schema.validate('12'), '12')
        self.assertEqual(schema.validate(1.2231), 1)

    def test_or_repr(self):
        schema = Or(1, str, Convert(lambda x: int(x)))
        self.assertTrue(
            str(schema).startswith(
                "<1 or <class 'str'> or <Convert: <function "))

    def test_and(self):
        schema = And(str, Convert(lambda x: int(x)))
        self.assertEqual(schema.validate('12'), 12)
        self.assertRaises(NotValid, schema.validate, 12.1)
        self.assertRaises(NotValid, schema.validate, 'foo')
        self.assertRaises(NotValid, schema.validate, '12.1')

    def test_and_repr(self):
        schema = And(str, Convert(lambda x: int(x)))
        self.assertTrue(
            str(schema).startswith(
                "<<class 'str'> and <Convert: <function "))

    def test_dont_care_values_in_dict(self):
        schema = Schema(
            {'foo': int,
             'bar': str,
             str: object})
        self.assertEqual(
            schema.validate(
                {'foo': 12,
                    'bar': 'bar',
                    'qux': 'baz',
                    'fnord': [1, 2, 'donkey kong']}),
            {'foo': 12,
             'bar': 'bar',
             'qux': 'baz',
             'fnord': [1, 2, 'donkey kong']})

    def test_callable(self):
        schema = Schema(lambda x: x < 2)
        self.assertEqual(schema.validate(1), 1)

    def test_callable_gives_readable_error(self):

        def less_than_two(value):
            """Must be less than two."""
            return value < 2

        schema = Schema(less_than_two)
        with self.assertRaises(NotValid) as ctx:
            schema.validate(12)
        self.assertEqual(
            ctx.exception.args,
            ("12 not validated by 'Must be less than two.'",))

    def test_callable_gives_sensible_error(self):

        def less_than_two(value):
            return value < 2

        schema = Schema(less_than_two)
        with self.assertRaises(NotValid) as ctx:
            schema.validate(12)
        self.assertEqual(
            ctx.exception.args,
            ("12 not validated by 'less_than_two'",))

    def test_convert(self):
        schema = Convert(lambda x: x + 2)
        self.assertEqual(schema.validate(1), 3)

    def test_ordered(self):
        schema = Ordered([str, int])
        self.assertTrue(schema.validates(['1', 3]))
        self.assertFalse(schema.validates([1, '3']))
        self.assertFalse(schema.validates(['1', 3, 4]))
        self.assertFalse(schema.validates(['1']))

    def test_ordered_repr(self):
        schema = Ordered([str, int])
        self.assertEqual(
            str(schema), "<Ordered: [<class 'str'>, <class 'int'>]>")

    def test_callable_exception(self):
        schema = Schema(lambda x: x + 2)
        self.assertRaises(NotValid, schema.validate, "foo")

    def test_subschemas(self):
        schema1 = Schema({'foo': str, str: int})
        schema2 = Schema(
            {'key1': schema1,
             'key2': schema1,
             str: schema1})
        self.assertTrue(schema2.validates(
            {'key1': {'foo': 'bar'},
             'key2': {'foo': 'qux', 'baz': 43},
             'whatever': {'foo': 'doo', 'fsck': 22, 'tsk': 2992}}))
        self.assertFalse(schema2.validates(
            {'key1': {'doo': 'bar'},
             'key2': {'foo': 'qux', 'baz': 43},
             'whatever': {'foo': 'doo', 'fsck': 22, 'tsk': 2992}}))
        self.assertFalse(schema2.validates(
            {'key1': {'doo': 'bar'},
             'key2': {'foo': 'qux', 12: 43},
             'whatever': {'foo': 'doo', 'fsck': 22, 'tsk': 2992}}))
        self.assertFalse(schema2.validates(
            {'key1': {'foo': 'bar'},
             'key2': {'foo': 'qux', 'baz': 'derp'},
             'whatever': {'foo': 'doo', 'fsck': 22, 'tsk': 2992}}))
        self.assertFalse(schema2.validates(
            {'key1': {'foo': 'bar'},
             'key2': {'foo': 'qux', 'baz': 'derp'},
             12: {'foo': 'doo', 'fsck': 22, 'tsk': 2992}}))
        self.assertFalse(schema2.validates(
            {'key1': {'foo': 'bar'},
             'key2': {'foo': 'qux', 'baz': 'derp'},
             'whatever': {}}))

# Translated Schema tests
    def test_and_schema(self):
        self.assertEqual(Schema(And(int, lambda n: 0 < n < 5)).validate(3), 3)
        self.assertRaises(
            NotValid, Schema(And(int, lambda n: 0 < n < 5)).validate, 3.33)
        self.assertEqual(
            Schema(And(Convert(int), lambda n: 0 < n < 5)).validate(3.33), 3)
        self.assertRaises(
            NotValid,
            Schema(And(Convert(int), lambda n: 0 < n < 5)).validate, '3.33')

    def test_or_schema(self):
        self.assertEqual(Schema(Or(int, dict)).validate(5), 5)
        self.assertEqual(Schema(Or(int, dict)).validate({}), {})
        with self.assertRaises(NotValid):
            Schema(Or(int, dict)).validate('hai')
        self.assertEqual(Schema(Or(int)).validate(4), 4)
        self.assertRaises(NotValid, Schema(Or()).validate, 2)

    def test_validate_list(self):
        self.assertEqual(Schema([1, 0]).validate([1, 0, 1, 1]), [1, 0, 1, 1])
        self.assertEqual(Schema([1, 0]).validate([]), [])
        self.assertRaises(NotValid, Schema([1, 0]).validate, 0)
        self.assertRaises(NotValid, Schema([1, 0]).validate, [2])
        self.assertEqual(Schema(
            And([1, 0], lambda l: len(l) > 2)).validate([0, 1, 0]), [0, 1, 0])
        self.assertRaises(
            NotValid,
            Schema(And([1, 0], lambda l: len(l) > 2)).validate, [0, 1])

    def test_list_tuple_set_frozenset(self):
        self.assertEqual(Schema([int]).validate([1, 2]), [1, 2])
        self.assertRaises(NotValid, Schema([int]).validate, ['1', 2])
        self.assertEqual(
            Schema(set([int])).validate(set([1, 2])), set([1, 2]))
        self.assertRaises(NotValid, Schema(set([int])).validate, [1, 2])
        self.assertRaises(NotValid, Schema(set([int])).validate, ['1', 2])
        self.assertEqual(
            Schema(tuple([int])).validate(tuple([1, 2])), tuple([1, 2]))
        self.assertRaises(NotValid, Schema(tuple([int])).validate, [1, 2])

    def test_strictly(self):
        self.assertEqual(Schema(int).validate(1), 1)
        self.assertRaises(NotValid, Schema(int).validate, '1')

    def test_dict(self):
        self.assertEqual(Schema({'key': 5}).validate({'key': 5}), {'key': 5})
        self.assertRaises(NotValid, Schema({'key': 5}).validate, {'key': 'x'})
        self.assertEqual(
            Schema({'key': int}).validate({'key': 5}), {'key': 5})
        self.assertEqual(
            Schema({'n': int, 'f': float}).validate({'n': 5, 'f': 3.14}),
            {'n': 5, 'f': 3.14})
        self.assertRaises(
            NotValid,
            Schema({'n': int, 'f': float}).validate, {'n': 3.14, 'f': 5})
        self.assertRaises(NotValid, Schema({'key': 5}).validate, {})
        self.assertRaises(NotValid, Schema({'key': 5}).validate, {'n': 5})
        self.assertRaises(NotValid, Schema({}).validate, {'n': 5})

    def test_dict_keys(self):
        self.assertEqual(
            Schema({str: int}).validate({'a': 1, 'b': 2}), {'a': 1, 'b': 2})
        self.assertRaises(
            NotValid, Schema({str: int}).validate, {1: 1, 'b': 2})
        # XXX: I don't intend to support this. Keys are literal,
        # Optional(literal) or type.
        # self.assertEqual(
        #    Schema({Convert(str): Convert(int)}).validate({1: 3.14, 3.14: 1}),
        #    {'1': 3, '3.14': 1})

    def test_dict_optional_keys(self):
        self.assertRaises(
            NotValid, Schema({Optional('a'): 1, 'b': 2}).validate, {'a': 1})
        self.assertEqual(
            Schema({'a': 1, Optional('b'): 2}).validate({'a': 1}), {'a': 1})
        self.assertEqual(
            Schema({'a': 1, Optional('b'): 2}).validate({'a': 1, 'b': 2}),
            {'a': 1, 'b': 2})
        self.assertRaises(
            NotValid, Schema({Optional('a'): 1}).validate, {'a': 2})

    def test_validate_object(self):
        schema = Schema({object: str})
        self.assertEqual(schema.validate({42: 'str'}), {42: 'str'})
        self.assertRaises(NotValid, schema.validate, {42: 777})

    def test_issue_9_prioritized_key_comparison(self):
        schema = Schema({'key': 42, object: 42})
        self.assertEqual(
            schema.validate({'key': 42, 777: 42}), {'key': 42, 777: 42})

    def test_issue_9_prioritized_key_comparison_in_dicts(self):
        # http://stackoverflow.com/questions/14588098/docopt-schema-validation
        schema = Schema(
            {'ID': Convert(int),  # , error='ID should be an int'),
             'FILE': Or(None, Convert(open)),  # , error='FILE not opened')),
             str: object})  # all type keys are optional
        data = {'ID': 10, 'FILE': None, 'other': 'other', 'other2': 'other2'}
        self.assertEqual(schema.validate(data), data)
        data = {'ID': 10, 'FILE': None}
        self.assertEqual(schema.validate(data), data)

    def test_schema_with_additional_validators(self):

        def total_greater_than_12(value):
            """foo + bar > 12"""
            return value['foo'] + value['bar'] > 12

        schema = Schema({
            'foo': int,
            'bar': int},
            additional_validators=(total_greater_than_12,))

        self.assertTrue(schema.validates({'foo': 7, 'bar': 7}))
        with self.assertRaises(NotValid) as ctx:
            schema.validate({'foo': 5, 'bar': 7})
        self.assertTrue(
            ctx.exception.args[0].endswith(
                "not validated by additional validator "
                "'foo + bar > 12'"))

    def test_documentation(self):
        result = doctest.testfile("README.rst")
        self.assertEqual(result.failed, 0)
