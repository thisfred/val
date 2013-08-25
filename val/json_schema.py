import json
import re
import requests
from val import Schema, Optional, Or, And, Not, NotValid, parse_schema


class OneOf(Schema):
    """Go home json-schema, you're drunk."""

    def __init__(self, *values):
        self.values = values
        self.schemas = tuple(parse_schema(s) for s in values)

    def validate(self, data):
        validated = 0
        for sub in self.schemas:
            try:
                data = sub(data)
            except NotValid:
                continue
            validated += 1
            if validated > 1:
                raise NotValid(
                    '%r validated by more than one of %r' % (
                        data, self.values))
        if not validated:
            raise NotValid(
                '%r validated not validated by %r' % (data, self.values))

        return data

    def __repr__(self):
        return "<%s>" % (" and ".join(["%r" % (v,) for v in self.values]),)


def hostname(value):
    if not isinstance(value, basestring):
        return False

    if not value[0].isalpha():
        return False

    for node in value.split('.'):
        if len(node) > 63:
            return False

        if not all((c.isalnum() or c == '-') for c in node):
            return False

    return True


def ipv6(value):
    if not isinstance(value, basestring):
        return False

    if len(value.split('::')) > 2:
        return False

    chunks = value.split(':')
    if len(chunks) > 8:
        return False

    for chunk in chunks:
        if len(chunk) > 4:
            return False

        if any(c.lower() not in 'abcdef01234567890' for c in chunk):
            return False

    return True


def ipv4(value):
    if not isinstance(value, basestring):
        return False

    chunks = value.split('.')
    if not len(chunks) == 4:
        return False

    for chunk in chunks:
        try:
            i = int(chunk)
        except ValueError:
            return False
        if i < 0 or i > 255:
            return False

    return True


def email(value):
    if not isinstance(value, basestring):
        return False

    user_host = value.split('@')
    if len(user_host) != 2:
        return False

    user, host = user_host
    if not hostname(host):
        return False

    return True


def uri(value):

    if not isinstance(value, basestring):
        return False

    scheme_rest = value.split(':')
    if len(scheme_rest) < 2:
        return False

    return True


def valid_hour(hour):
    if len(hour) != 2:
        return False
    try:
        hour = int(hour)
    except ValueError:
        return False
    if hour < 0 or hour > 23:
        return False
    return True


def valid_second_or_minute(value):
    if len(value) != 2:
        return False
    try:
        value = int(value)
    except ValueError:
        return False
    if value < 0 or value > 59:
        return False
    return True


def datetime(value):

    if not isinstance(value, basestring):
        return False

    if not 'T' in value:
        return False

    date, time = value.split('T')
    date_chunks = date.split('-')
    if not len(date_chunks) == 3:
        return False

    year, month, day = date_chunks
    if not len(year) == 4:
        return False

    try:
        int(year)
    except ValueError:
        return False

    if not len(month) == 2:
        return False

    try:
        month = int(month)
    except ValueError:
        return False

    if month < 1 or month > 12:
        return False

    if not len(day) == 2:
        return False

    try:
        day = int(day)
    except ValueError:
        return False

    if day < 1 or day > 31:
        return False

    if '-' in time:
        time, tz = time.split('-')
    elif '+' in time:
        time, tz = time.split('+')
    else:
        if not time.endswith('Z'):
            return False
        time = time[:-1]
        tz = None
    if tz:
        tz = tz.split(':')
        if len(tz) != 2:
            return False
        hour, minute = tz
        if not valid_hour(hour):
            return False
        if not valid_second_or_minute(minute):
            return False

    if '.' in time:
        time, sec_frag = time.split('.')
        try:
            int(sec_frag)
        except ValueError:
            return False

    time = time.split(':')
    if len(time) != 3:
        return False
    hour, minute, second = time
    return (
        valid_hour(hour) and valid_second_or_minute(minute) and
        valid_second_or_minute(second))


FORMAT_CHECKERS = {
    'date-time': datetime,
    'email': email,
    'hostname': hostname,
    'ipv4': ipv4,
    'ipv6': ipv6,
    'uri': uri,
    'regex': str}

integer = And(int, lambda x: not isinstance(x, bool))

TYPE_CHECKERS = {
    'array': list,
    'boolean': bool,
    'integer': Or(integer, long),
    'number': Or(integer, float, long),
    'null': None,
    'object': dict,
    'string': basestring}


def not_a_number(value):
    if isinstance(value, int):
        return False
    if isinstance(value, float):
        return False
    if isinstance(value, long):
        return False
    return True


def not_a_string(value):
    return not isinstance(value, basestring)


def not_an_array(value):
    return not isinstance(value, list)


def not_an_object(value):
    return not isinstance(value, dict)


def get_multiple_validator(divisor):
    divisor = float(divisor)
    return lambda x: not_a_number(x) or ((x / divisor) == int(x / divisor))


def get_maximum_validator(maximum, exclusive):
    if exclusive:
        return lambda x: not_a_number(x) or x < maximum
    return lambda x: not_a_number(x) or x <= maximum


def get_minimum_validator(minimum, exclusive):
    if exclusive:
        return lambda x: not_a_number(x) or x > minimum
    return lambda x: not_a_number(x) or x >= minimum


def get_has_keys_validator(keys):
    return lambda x: all(key in x for key in keys)


def parse_dependency(dependency):
    if isinstance(dependency, list):
        return Schema(get_has_keys_validator(dependency))

    return parse_json_schema(dependency)


def get_dependencies_validator(dependencies):
    validators = {
        key: parse_dependency(dep) for key, dep in dependencies.items()}

    def validator(value):
        if not isinstance(value, dict):
            return True

        for key, subschema in validators.items():
            if key in value:
                subschema.validate(value)

        return True

    return validator


def get_properties_validator(properties, additional_properties,
                             pattern_properties):
    validator = {
        key: parse_json_schema(prop) for key, prop in properties.items()}
    if additional_properties is True:
        validator[object] = object
    elif additional_properties is not False:
        validator[object] = parse_json_schema(additional_properties)
    for key, value in pattern_properties.items():

        def get_f(pattern):
            def f(x):
                print key, x, pattern.findall(x)
                return pattern.findall(x) != []
            return f

        pattern = re.compile(key)
        validator[Optional(get_f(pattern))] = parse_json_schema(value)
    return Or(not_an_object, validator)


def get_items_validator(items, additional_items):
    if isinstance(items, dict):
        return Or(not_an_array, [parse_json_schema(items)])

    validators = [parse_json_schema(i) for i in items]
    if isinstance(additional_items, dict):
        additional_item_validator = parse_json_schema(additional_items)

    def validate(value):
        if not isinstance(value, list):
            return True

        if len(value) < len(validators):
            return False

        to_validate = value[:]
        for validator in validators:
            validator.validate(to_validate.pop(0))

        if not to_validate:
            return True

        if additional_items is True:
            return True

        if additional_items is False:
            return False

        for extra in to_validate:
            if not additional_item_validator.validates(extra):
                return False

        return True

    return validate


def get_min_items_validator(number):
    return lambda x: not_an_array(x) or len(x) >= number


def unique_items_validator(value):
    # XXX: nasty hack to make sure True is not seen as 1
    seen = set()
    for v in value:
        if repr(v) in seen:
            return False
        seen.add(repr(v))
    return True


NO_SCHEMA = object()


def combine(schema1, schema2):
    if schema1 is NO_SCHEMA:
        return schema2
    if schema2 is NO_SCHEMA:
        return schema1
    return And(schema1, schema2)


def parse_json_schema(schema):
    result = NO_SCHEMA
    if schema == {}:
        return Schema(object)
    if 'format' in schema:
        result = combine(result, FORMAT_CHECKERS[schema['format']])
    if 'type' in schema:
        types = schema['type']
        if isinstance(types, list):
            result = combine(result, Or(*[TYPE_CHECKERS[t] for t in types]))
        else:
            result = combine(result, TYPE_CHECKERS[types])
    if 'multipleOf' in schema:
        divisor = schema['multipleOf']
        result = combine(result, get_multiple_validator(divisor))
    if 'maximum' in schema:
        maximum = schema['maximum']
        result = combine(result, get_maximum_validator(
            maximum, exclusive=schema.get('exclusiveMaximum', False)))
    if 'minimum' in schema:
        minimum = schema['minimum']
        result = combine(result, get_minimum_validator(
            minimum, exclusive=schema.get('exclusiveMinimum', False)))
    if 'dependencies' in schema:
        dependencies = schema['dependencies']
        result = combine(result, get_dependencies_validator(dependencies))
    if ('properties' in schema or 'patternProperties' in schema or
            'additionalProperties' in schema):
        properties = schema.get('properties', {})
        additional_properties = schema.get('additionalProperties', {})
        pattern_properties = schema.get('patternProperties', {})
        result = combine(
            result,
            get_properties_validator(
                properties, additional_properties=additional_properties,
                pattern_properties=pattern_properties))
    if 'minProperties' in schema:
        result = combine(
            result, Or(
                not_an_object,
                lambda x: len(x.keys()) >= schema['minProperties']))
    if 'anyOf' in schema:
        result = combine(
            result, Or(*[parse_json_schema(s) for s in schema['anyOf']]))
    if 'allOf' in schema:
        result = combine(
            result, And(*[parse_json_schema(s) for s in schema['allOf']]))
    if 'oneOf' in schema:
        result = combine(
            result, OneOf(*[parse_json_schema(s) for s in schema['oneOf']]))
    if 'minLength' in schema:
        result = combine(
            result, lambda x: not_a_string(x) or len(x) >= schema['minLength'])
    if 'maxLength' in schema:
        result = combine(
            result, lambda x: not_a_string(x) or len(x) <= schema['maxLength'])
    if 'items' in schema or 'additionalItems' in schema:
        additional_items = schema.get('additionalItems', {})
        result = combine(
            result,
            get_items_validator(
                schema.get('items', {}), additional_items=additional_items))
    if 'minItems' in schema:
        result = combine(result, get_min_items_validator(schema['minItems']))
    if 'not' in schema:
        result = combine(result, Not(parse_json_schema(schema['not'])))
    if 'uniqueItems' in schema:
        if schema['uniqueItems']:
            result = combine(result, unique_items_validator)
    if '$ref' in schema:
        ref = schema['$ref']
        if ref.startswith('http'):
            remote = json.loads(requests.get(ref).content)
            result = combine(result, parse_json_schema(remote))
    return Schema(result)
