from lazyval import validate, validates, NotValid, Optional
from unittest import TestCase

lazy_schema = {
    Optional('invisible'): bool,
    Optional('immutable'): bool,
    Optional('favorite_colors'): [str],
    Optional('favorite_foods'): [str],
    Optional('lucky_number'): [int, None],
    Optional('shoe_size'): int,
    Optional('mother'): {
        'name': str,
        'nested': {'id': str}},
    Optional('father'): {
        'name': str,
        'nested': {'id': str}}}


TYPICAL_TEST_DATA = {
    'invisible': False,
    'immutable': False,
    'favorite_colors': [],
    'favorite_foods': [],
    'lucky_number': 1,
    'shoe_size': 12,
    'mother': {
        'name': 'edna',
        'nested': {'id': '1232134'}},
    'father': {
        'name': 'ed',
        'nested': {'id': '9492921'}}}

INVALID_TEST_DATA = {
    'invisible': False,
    'immutable': 0,
    'favorite_colors': [],
    'favorite_foods': [],
    'lucky_number': 1,
    'shoe_size': 12,
    'mother': 'edna',
    'father': {
        'name': 'ed',
        'nested': {'id': '9492921'}}}


class TestLazyval(TestCase):

    def test_identity(self):
        self.assertEquals(validate('test', 'test'), 'test')

    def test_non_identity(self):
        self.assertRaises(NotValid, validate, 'foo', 'bar')

    def test_validates_true(self):
        self.assertEquals(validates('foo', 'foo'), True)

    def test_validates_false(self):
        self.assertEquals(validates('foo', 'bar'), False)

    def test_type_check(self):
        self.assertEquals(validate(str, 'test'), 'test')

    def test_failing_type_check(self):
        self.assertRaises(NotValid, validate, int, 'test')

    def test_dictionary(self):
        self.assertEquals(
            validate({'key': str}, {'key': 'val'}), {'key': 'val'})

    def test_dictionary_optional(self):
        self.assertEquals(
            validate({'key': str, Optional('key2'): str}, {'key': 'val'}),
            {'key': 'val'})

    def test_dictionary_wrong_key(self):
        self.assertRaises(NotValid, validate, {'key': str}, {'not_key': 'val'})

    def test_dictionary_missing_key(self):
        self.assertRaises(
            NotValid, validate, {'key': str, 'key2': str}, {'key': 'val'})

    def test_list_data(self):
        self.assertTrue(validates([str], ['1', '2', '3']))

    def test_list_data_wrong_type(self):
        self.assertFalse(validates([str], ['1', '2', 3]))

    def test_list_data_multiple_types(self):
        self.assertTrue(validates([str, int], ['1', '2', 3]))

    def test_list_schema(self):
        self.assertTrue(validates(['1', '2', '3'], '1'))

    def test_list_schema_not_found(self):
        self.assertFalse(validates(['1', '2', '3'], '12'))

    def test_dont_care_values_in_dict(self):
        self.assertEquals(
            validate(
                {'foo': int,
                 'bar': str,
                 str: object},
                {'foo': 12,
                 'bar': 'bar',
                 'qux': 'baz',
                 'fnord': [1, 2, 'donkey kong']}),
            {'foo': 12,
             'bar': 'bar',
             'qux': 'baz',
             'fnord': [1, 2, 'donkey kong']})

    def test_matching_key_invalid_value(self):
        self.assertFalse(
            validates(
                {'foo': int,
                 'bar': str,
                 str: str},
                {'foo': 12,
                 'bar': 'bar',
                 'qux': 'baz',
                 'fnord': [1, 2, 'donkey kong']}))

    def test_schema_valid(self):
        self.assertEquals(
            validate(lazy_schema, TYPICAL_TEST_DATA), TYPICAL_TEST_DATA)

    def test_schema_invalid(self):
        self.assertRaises(NotValid, validate, lazy_schema, INVALID_TEST_DATA)
