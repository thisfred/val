from tempfile import mkstemp
from val import validate, validates, NotValid, Optional, Or, Schema
from unittest import TestCase
from hotshot import Profile, stats

LAZY_SCHEMA = {
    Optional('invisible'): bool,
    Optional('immutable'): bool,
    Optional('favorite_colors'): [str],
    Optional('favorite_foods'): [str],
    Optional('lucky_number'): Or(int, None),
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
    'favorite_colors': ['mauve', 'taupe', 'beige'],
    'favorite_foods': ['granola', 'shinola'],
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
    'favorite_colors': ['test', 'test2', None, 1233, 1.34, False],
    'favorite_foods': ['kraft cheese'],
    'lucky_number': 1,
    'shoe_size': 12,
    'mother': 'edna',
    'father': {
        'name': 'ed',
        'nested': {'id': '9492921'}}}


class TestLazyval(TestCase):

    def test_identity(self):
        self.assertEquals(validate('test', 'test'), 'test')

    def test_identity_schema(self):
        schema = Schema('test')
        self.assertEquals(schema.validate('test'), 'test')

    def test_non_identity(self):
        self.assertRaises(NotValid, validate, 'foo', 'bar')

    def test_non_identity_schema(self):
        schema = Schema('test')
        self.assertRaises(NotValid, schema.validate, 'bar')

    def test_validates_true(self):
        self.assertEquals(validates('foo', 'foo'), True)

    def test_validates_false(self):
        self.assertEquals(validates('foo', 'bar'), False)

    def test_type_check(self):
        self.assertEquals(validate(str, 'test'), 'test')

    def test_type_check_schema(self):
        schema = Schema(str)
        self.assertEquals(schema.validate('test'), 'test')

    def test_failing_type_check(self):
        self.assertRaises(NotValid, validate, int, 'test')

    def test_failing_type_check_schema(self):
        schema = Schema(int)
        self.assertRaises(NotValid, schema.validate, 'test')

    def test_dictionary(self):
        self.assertEquals(
            validate({'key': str}, {'key': 'val'}), {'key': 'val'})

    def test_dictionary_schema(self):
        schema = Schema({'key': str})
        self.assertEquals(schema.validate({'key': 'val'}), {'key': 'val'})

    def test_dictionary_optional(self):
        self.assertEquals(
            validate({'key': str, Optional('key2'): str}, {'key': 'val'}),
            {'key': 'val'})

    def test_dictionary_optional_schema(self):
        schema = Schema({'key': str, Optional('key2'): str})
        self.assertEquals(schema.validate({'key': 'val'}), {'key': 'val'})

    def test_dictionary_wrong_key(self):
        self.assertRaises(NotValid, validate, {'key': str}, {'not_key': 'val'})

    def test_dictionary_wrong_key_schema(self):
        schema = Schema({'key': str})
        self.assertRaises(NotValid, schema.validate, {'not_key': 'val'})

    def test_dictionary_missing_key(self):
        self.assertRaises(
            NotValid, validate, {'key': str, 'key2': str}, {'key': 'val'})

    def test_dictionary_missing_key_schema(self):
        schema = Schema({'key': str, 'key2': str})
        self.assertRaises(NotValid, schema.validate, {'key': 'val'})

    def test_list_data(self):
        self.assertTrue(validates([str], ['1', '2', '3']))

    def test_list_data_schema(self):
        schema = Schema([str])
        self.assertTrue(schema.validates(['1', '2', '3']))

    def test_list_data_wrong_type(self):
        self.assertFalse(validates([str], ['1', '2', 3]))

    def test_list_data_wrong_type_schema(self):
        schema = Schema([str])
        self.assertFalse(schema.validates(['1', '2', 3]))

    def test_list_data_multiple_types(self):
        self.assertTrue(validates([str, int], ['1', '2', 3]))

    def test_list_data_multiple_types_schema(self):
        schema = Schema([str, int])
        self.assertTrue(schema.validates(['1', '2', 3]))

    def test_not_list(self):
        self.assertFalse(validates(['1', '2', '3'], '1'))

    def test_not_list_schema(self):
        schema = Schema(['1', '2', '3'])
        self.assertFalse(schema.validates('1'))

    def test_or(self):
        self.assertTrue(validates(Or('1', '2', '3'), '1'))

    def test_or_schema(self):
        schema = Schema(Or('1', '2', '3'))
        self.assertTrue(schema.validates('1'))

    def test_list_not_found(self):
        self.assertFalse(validates(['1', '2', '3'], '12'))

    def test_list_not_found_schema(self):
        schema = Schema(['1', '2', '3'])
        self.assertFalse(schema.validates('12'))

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

    def test_dont_care_values_in_dict_schema(self):
        schema = Schema(
            {'foo': int,
             'bar': str,
             str: object})
        self.assertEquals(
            schema.validate(
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
            validate(LAZY_SCHEMA, TYPICAL_TEST_DATA), TYPICAL_TEST_DATA)

    def test_schema_invalid(self):
        self.assertRaises(NotValid, validate, LAZY_SCHEMA, INVALID_TEST_DATA)

    def test_functional_validation_profile(self):
        tmp_file, filename = mkstemp()
        profile = Profile(filename)
        result = profile.runcall(validate, LAZY_SCHEMA, TYPICAL_TEST_DATA)
        st = stats.load(filename)
        st.strip_dirs()
        st.sort_stats('time', 'calls')
        st.print_stats(20)
        self.assertTrue(result)
        self.fail()

    def test_schema_parsing_profile(self):
        tmp_file, filename = mkstemp()
        profile = Profile(filename)
        lazy_schema = Schema(LAZY_SCHEMA)
        result = profile.runcall(lazy_schema.validate, TYPICAL_TEST_DATA)
        st = stats.load(filename)
        st.strip_dirs()
        st.sort_stats('time', 'calls')
        st.print_stats(20)
        self.assertTrue(result)
        self.fail()
