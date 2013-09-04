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
                '%r not validated by %r' % (data, self.values))

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


def get_multiple_validator(divisor, lookup, path):
    divisor = float(divisor)
    return lambda x: not_a_number(x) or ((x / divisor) == int(x / divisor))


def get_maximum_validator(schema, lookup, path):
    maximum = schema['maximum']
    exclusive = schema.get('exclusiveMaximum', False)
    if exclusive:
        validator = lambda x: not_a_number(x) or x < maximum
    else:
        validator = lambda x: not_a_number(x) or x <= maximum
    lookup.add(path, 'maximum', validator)
    lookup.add(path, 'exclusiveMaximum', exclusive)
    return validator


def get_minimum_validator(schema, lookup, path):
    minimum = schema['minimum']
    exclusive = schema.get('exclusiveMinimum', False)
    if exclusive:
        validator = lambda x: not_a_number(x) or x > minimum
    else:
        validator = lambda x: not_a_number(x) or x >= minimum
    lookup.add(path, 'minimum', validator)
    lookup.add(path, 'exclusiveMinimum', exclusive)
    return validator


def get_has_keys_validator(keys):
    return lambda x: all(key in x for key in keys)


def get_min_items_validator(number, lookup, path):
    return lambda x: not_an_array(x) or len(x) >= number


def get_pattern_validator(pattern, lookup, path):
    regex = re.compile(pattern)
    return lambda x: regex.findall(x) != []


def unique_items_validator(value):
    # XXX: nasty hack to make sure True is not seen as 1
    seen = set()
    for v in value:
        if repr(v) in seen:
            return False
        seen.add(repr(v))
    return True


def parse_dependency(dependency, lookup, path):
    if isinstance(dependency, list):
        return Schema(get_has_keys_validator(dependency))

    return _parse_json_schema(dependency, lookup, path).to_val()


def get_dependencies_validator(dependencies, lookup, path):
    validators = {
        key: parse_dependency(dep, lookup, path + (key,)) for key, dep in
        dependencies.items()}

    def validator(value):
        if not isinstance(value, dict):
            return True

        for key, subschema in validators.items():
            if key in value:
                subschema.validate(value)

        return True

    return validator


def _get_object_validator(schema, properties, additional_properties,
                          pattern_properties, lookup, path):
    if additional_properties is not False:
        return lambda data: True

    p = tuple(properties.keys())
    pp = tuple(
        get_pattern_validator(k, None, None) for k in
        pattern_properties.keys())

    def validate(data):
        s = data.keys()
        for key in p:
            if key in s:
                s.remove(key)
        for key in s[:]:
            for pattern in pp:
                if pattern(key):
                    s.remove(key)
                    break
        if s:
            return False

        return True

    return validate


def _get_object_children_validator(schema, properties, additional_properties,
                                   pattern_properties, lookup, path):
    validator = {}
    sub_path = path + ('properties',)
    for key, prop in properties.items():
        sub_validator = _parse_json_schema(
            prop, lookup, sub_path + (key,)).to_val()
        validator[Optional(key)] = sub_validator
    if additional_properties is True or additional_properties == {}:
        validator[object] = object
    elif additional_properties is not False:
        sub_validator = _parse_json_schema(
            additional_properties, lookup,
            path + ('additionalProperties',)).to_val()
        validator[object] = sub_validator
    if pattern_properties:
        sub_path = path + ('patternProperties',)
        for key, value in pattern_properties.items():
            sub_validator = _parse_json_schema(
                value, lookup, sub_path + (key,)).to_val()
            validator[
                Optional(
                    get_pattern_validator(key, None, None))] = sub_validator
    return validator


def get_properties_validator(schema, lookup, path):
    properties = schema.get('properties', {})
    additional_properties = schema.get('additionalProperties', {})
    pattern_properties = schema.get('patternProperties', {})
    object_validator = _get_object_validator(
        schema, properties, additional_properties, pattern_properties, lookup,
        path)
    children_validator = _get_object_children_validator(
        schema, properties, additional_properties, pattern_properties, lookup,
        path)
    validator = Or(not_an_object, And(object_validator, children_validator))
    lookup.add(path, None, validator)
    return validator


def _get_array_validator(schema, items, additional_items, lookup, path):
    if isinstance(items, dict):
        return lambda data: True

    if additional_items is True or isinstance(additional_items, dict):
        return lambda data: True

    return lambda data: not isinstance(data, list) or len(data) <= len(items)


def _get_array_children_validator(schema, items, additional_items, lookup,
                                  path):
    if isinstance(items, dict):
        validator = Or(
            not_an_array,
            [_parse_json_schema(items, lookup, path + ('items',)).to_val()])
        lookup.add(path, 'items', validator)
        return validator

    validators = [
        _parse_json_schema(i, lookup, path + ('items', '%d' % n)).to_val() for
        n, i in enumerate(items)]
    if isinstance(additional_items, dict):
        additional_item_validator = _parse_json_schema(
            additional_items, lookup, path + ('additionalItems',)).to_val()

    def validate(data):
        to_validate = data[:]
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


def get_items_validator(schema, lookup, path):
    items = schema.get('items', {})
    additional_items = schema.get('additionalItems', {})
    array_validator = _get_array_validator(
        schema, items, additional_items, lookup, path)
    children_validator = _get_array_children_validator(
        schema, items, additional_items, lookup, path)
    validator = And(array_validator, children_validator)
    lookup.add(path, None, validator)
    return validator


def get_required_validator(schema, lookup, path):
    validator = {k: object for k in schema}
    validator[object] = object
    return Schema(validator)


def get_internal_reference_validator(lookup, path):

    def validate(data):
        validator = lookup.get(tuple(path.split('/')))
        return validator.validates(data)

    return validate


def get_ref_validator(schema, lookup, path):
    ref = schema['$ref']
    if ref.startswith('http'):
        remote = lookup.get_remote(ref)
        validator = _parse_json_schema(remote, lookup, path).to_val()
    else:
        scope = lookup.resolve_scope(path, ref)
        if scope.startswith('http'):
            remote = lookup.get_remote(ref)
            validator = _parse_json_schema(remote, lookup, path).to_val()
        else:
            validator = get_internal_reference_validator(lookup, ref)
            lookup.add_reference(ref)
    return validator


def parse_definitions(schema, lookup, path):
    for key, value in schema.items():
        lookup.add(
            path, key, _parse_json_schema(
                value, lookup, path + (key,)).to_val())


integer = And(int, Not(bool))

FORMAT_CHECKERS = {
    'date-time': datetime,
    'email': email,
    'hostname': hostname,
    'ipv4': ipv4,
    'ipv6': ipv6,
    'uri': uri,
    'regex': str}

TYPE_CHECKERS = {
    'array': list,
    'boolean': bool,
    'integer': Or(integer, long),
    'null': None,
    'number': Or(integer, float, long),
    'object': dict,
    'string': basestring}

SIMPLE_VALIDATORS = {
    'enum': lambda x, lookup, path: Or(*x),
    'format': lambda x, lookup, path: FORMAT_CHECKERS[x],
    'type': lambda x, lookup, path: Or(
        *[TYPE_CHECKERS[t] for t in x]) if isinstance(x, list) else
        TYPE_CHECKERS[x],
    'multipleOf': get_multiple_validator,
    'dependencies': get_dependencies_validator,
    'pattern': get_pattern_validator,
    'anyOf': lambda x, lookup, path: Or(
        *[_parse_json_schema(s, lookup, path + ('%d' % n,)).to_val() for n, s
          in enumerate(x)]),
    'allOf': lambda x, lookup, path: And(
        *[_parse_json_schema(s, lookup, path + ('%d' % n,)).to_val() for n, s
          in enumerate(x)]),
    'minLength':
        lambda x, lookup, path: lambda data: not_a_string(
            data) or len(data) >= x,
    'maxLength':
        lambda x, lookup, path: lambda data: not_a_string(
            data) or len(data) <= x,
    'maxItems': lambda x, lookup, path:
        lambda data: not_an_array(data) or len(data) <= x,
    'not': lambda x, lookup, path: Not(_parse_json_schema(
        x, lookup, path).to_val()),
    'uniqueItems': lambda x, lookup, path:
        unique_items_validator if x else lambda data: data,
    'required': get_required_validator,
    'minItems': get_min_items_validator,
    'oneOf': lambda x, lookup, path: OneOf(
        *[_parse_json_schema(s, lookup, path + ('%d' % n,)).to_val() for n, s
          in enumerate(x)]),
    'minProperties': lambda x, lookup, path: Or(
        not_an_object, lambda data: len(data.keys()) >= x)}

COMPOUND_VALIDATORS = {
    ('maximum', 'exclusiveMaximum'): get_maximum_validator,
    ('minimum', 'exclusiveMinimum'): get_minimum_validator,
    ('properties', 'patternProperties', 'additionalProperties'):
        get_properties_validator,
    ('items', 'additionalItems'): get_items_validator,
    ('$ref',): get_ref_validator}

NON_VALIDATORS = {
    'default': lambda x, lookup, path: x,
    'definitions': parse_definitions,
    'id': lambda x, lookup, path: lookup.add_scope(path, x)}


class Parsed(object):

    def __init__(self):
        self.validators = []
        self.lookup = None

    def to_val(self):
        if len(self.validators) == 1:
            return Schema(self.validators[0])
        else:
            return And(*self.validators)

    def add_validator(self, validator):
        self.validators.append(validator)


class Lookup(object):

    def __init__(self):
        self._lookup = {}
        self._references = []
        self._scopes = {}
        self._cache = {}

    def __repr__(self):
        return repr(self._lookup)

    def __str__(self):
        return str(self._lookup)

    def get(self, path):
        try:
            return self._lookup[path]
        except KeyError:
            raise NotValid("%s is not a valid reference." % path)

    def get_remote(self, address):
        if '#' in address:
            address, path = address.split('#')
        else:
            path = ''
        if address not in self._cache:
            self._cache[address] = json.loads(requests.get(address).content)
        document = self._cache[address]
        return document

    def add(self, path, key, value):
        if key is None:
            self._lookup[path] = value
        else:
            self._lookup[path + (key,)] = value

    def add_reference(self, path):
        self._references.append(tuple(path.split('/')))

    def add_scope(self, path, new_id):
        path_minus_id = path[:-1]
        self._scopes[path_minus_id] = new_id
        return self._scopes[path_minus_id]

    def resolve_scope(self, path, ref):
        scopes = sorted(
            (k, v) for k, v in self._scopes.items() if path[:len(k)] == k)
        print scopes
        result = ''
        for s in [v for _, v in scopes] + [ref]:
            if result and result[-1] == '#' and v[0] == '#':
                result += s[1:]
            else:
                result += s
        return result

    def cleanup(self):
        self._lookup = {
            k: v for k, v in self._lookup.items() if k in self._references}


def _parse_json_schema(schema, lookup=None, path=None):
    if not isinstance(schema, dict):
        lookup.add(path, None, schema)
        return schema
    if lookup is None:
        lookup = Lookup()
    if path is None:
        path = ('#',)
    parsed = Parsed()
    for key in NON_VALIDATORS:
        if key in schema:
            lookup.add(
                path, key,
                NON_VALIDATORS[key](schema[key], lookup, path + (key,)))
    skip = ['$schema', 'description'] + NON_VALIDATORS.keys()
    for key, value in schema.items():
        if key in skip:
            continue
        if key in SIMPLE_VALIDATORS:
            validator = SIMPLE_VALIDATORS[key](
                schema[key], lookup, path + (key,))
            parsed.add_validator(validator)
            lookup.add(path, key, validator)
            continue
        found = False
        for validator_key in COMPOUND_VALIDATORS:
            if key == validator_key or key in validator_key:
                if isinstance(validator_key, tuple):
                    skip.extend(list(validator_key))
                validator = COMPOUND_VALIDATORS[validator_key](
                    schema, lookup, path)
                parsed.add_validator(validator)
                found = True
                break
        if found:
            continue
        validator = _parse_json_schema(value, lookup, path + (key,))
        parsed.add_validator(validator)
        lookup.add(path, key, validator)
    lookup.add(path, None, parsed.to_val())
    parsed.lookup = lookup
    return parsed


def parse_json_schema(json_schema):
    parsed = _parse_json_schema(json_schema)
    parsed.lookup.cleanup()
    return parsed.to_val()
