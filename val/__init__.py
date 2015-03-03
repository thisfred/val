"""
val: A validator for arbitrary python objects.

Copyright (c) 2013-2015
Eric Casteleijn, <thisfred@gmail.com>
"""

__version__ = '0.8dev'
UNSPECIFIED = object()


class NotValid(Exception):

    """Object not valid for schema."""

    pass


def get_repr(thing):
    """Get sensible string representation for validator."""
    return (
        getattr(thing, '__doc__') or
        getattr(thing, '__name__') or
        repr(thing))


def build_type_validator(value_type):
    """Build a validator that only checks the type of a value."""

    def type_validator(data):
        """Validate instances of a particular type."""
        if isinstance(data, value_type):
            return data

        raise NotValid('%r is not of type %r' % (data, value_type))

    return type_validator


def build_static_validator(exact_value):
    """Build a validator that checks if the data is equal to an exact value."""

    def static_validator(data):
        """Validate by equality."""
        if data == exact_value:
            return data

        raise NotValid('%r is not equal to %r' % (data, exact_value))

    return static_validator


def build_callable_validator(function):
    """Build a validator that checks the return value of function(data)."""

    def callable_validator(data):
        """Validate by checking the return value of function(data)."""
        try:
            if function(data):
                return data

        except (TypeError, ValueError, NotValid) as ex:
            raise NotValid(ex.args)

        raise NotValid("%r invalidated by '%s'" % (data, get_repr(function)))

    return callable_validator


def build_iterable_validator(iterable):
    """Build a validator from an iterable."""
    sub_schemas = [parse_schema(s) for s in iterable]

    def item_validator(value):
        """Validate items in an iterable."""
        for sub in sub_schemas:
            try:
                return sub(value)

            except NotValid:
                pass

        raise NotValid('%r invalidated by anything in %s.' % (value, iterable))

    def iterable_validator(data):
        """Validate an iterable."""
        if not type(data) is type(iterable):
            raise NotValid('%r is not of type %s' % (data, type(iterable)))

        return type(iterable)(item_validator(value) for value in data)

    return iterable_validator


def _determine_keys(dictionary):
    """Determine the different kinds of keys."""
    optional = {}
    defaults = {}
    mandatory = {}
    types = {}
    for key, value in dictionary.items():
        if isinstance(key, Optional):
            optional[key.value] = parse_schema(value)
            if isinstance(value, BaseSchema) and\
                    value.default is not UNSPECIFIED:
                defaults[key.value] = (value.default, value.null_values)
            continue  # pragma: nocover

        if type(key) is type:
            types[key] = parse_schema(value)
            continue

        mandatory[key] = parse_schema(value)
    return mandatory, optional, types, defaults


def _validate_mandatory_keys(mandatory, validated, data, to_validate):
    """Validate the manditory keys."""
    errors = []
    for key, sub_schema in mandatory.items():
        if key not in data:
            errors.append('missing key: %r' % (key,))
            continue
        try:
            validated[key] = sub_schema(data[key])
        except NotValid as ex:
            errors.extend(['%r: %s' % (key, arg) for arg in ex.args])
        to_validate.remove(key)
    return errors


def _validate_optional_key(key, missing, value, validated, optional):
    """Validate an optional key."""
    try:
        validated[key] = optional[key](value)
    except NotValid as ex:
        return ['%r: %s' % (key, arg) for arg in ex.args]
    if key in missing:
        missing.remove(key)
    return []


def _validate_type_key(key, value, types, validated):
    """Validate a key's value by type."""
    for key_schema, value_schema in types.items():
        if not isinstance(key, key_schema):
            continue
        try:
            validated[key] = value_schema(value)
        except NotValid:
            continue
        else:
            return []

    return ['%r: %r not matched' % (key, value)]


def _validate_other_keys(optional, types, missing, validated, data,
                         to_validate):
    """Validate the rest of the keys present in the data."""
    errors = []
    for key in to_validate:
        value = data[key]
        if key in optional:
            errors.extend(
                _validate_optional_key(
                    key, missing, value, validated, optional))
            continue
        errors.extend(_validate_type_key(key, value, types, validated))
    return errors


def build_dict_validator(dictionary):
    """Build a validator from a dictionary."""
    mandatory, optional, types, defaults = _determine_keys(dictionary)

    def dict_validator(data):
        """Validate dictionaries."""
        missing = list(defaults.keys())
        if not isinstance(data, dict):
            raise NotValid('%r is not of type dict' % (data,))

        validated = {}
        to_validate = list(data.keys())
        errors = _validate_mandatory_keys(
            mandatory, validated, data, to_validate)
        errors.extend(
            _validate_other_keys(
                optional, types, missing, validated, data, to_validate))
        if errors:
            raise NotValid(*errors)
        for key in missing:
            validated[key] = defaults[key][0]

        return validated

    return dict_validator


def parse_schema(schema):
    """Parse a val schema definition."""

    if isinstance(schema, BaseSchema):
        return schema.validate

    if type(schema) is type:
        return build_type_validator(schema)

    if isinstance(schema, dict):
        return build_dict_validator(schema)

    if type(schema) in (list, tuple, set):
        return build_iterable_validator(schema)

    if callable(schema):
        return build_callable_validator(schema)

    return build_static_validator(schema)


class BaseSchema(object):

    """Base class for all Schema objects."""

    def __init__(self, additional_validators=None, default=UNSPECIFIED,
                 null_values=UNSPECIFIED):
        """Fallback constructor."""
        self.additional_validators = additional_validators or []
        self.default = default
        self.null_values = null_values
        self.annotations = {}

    def validates(self, data):
        """Return True if schema validates data, False otherwise."""
        try:
            self.validate(data)
            return True
        except NotValid:
            return False

    def _validated(self, data):
        """Return validated data."""
        raise NotImplementedError

    def validate(self, data):
        """Validate data. Raise NotValid error for invalid data."""
        validated = self._validated(data)
        errors = []
        for validator in self.additional_validators:
            if not validator(validated):
                errors.append(
                    "%s invalidated by '%s'" % (
                        validated, get_repr(validator)))
        if errors:
            raise NotValid(*errors)

        if self.default is UNSPECIFIED:
            return validated

        if self.null_values is not UNSPECIFIED\
                and validated in self.null_values:
            return self.default

        if validated is None:
            return self.default

        return validated


class Schema(BaseSchema):

    """A val schema."""

    def __init__(self, schema, **kwargs):
        super(Schema, self).__init__(**kwargs)
        self._definition = schema
        self.schema = parse_schema(schema)

    @property
    def definition(self):
        """Definition with which this schema was initialized."""
        return self._definition

    def __repr__(self):
        return repr(self.definition)

    def _validated(self, data):
        return self.schema(data)


class Optional(object):

    """Optional key in a dictionary."""

    def __init__(self, value):
        """Optional key in a dictionary."""
        self.value = value

    def __repr__(self):
        return "<Optional: %r>" % (self.value,)


class Or(BaseSchema):

    """Validates if any of the subschemas do."""

    def __init__(self, *values, **kwargs):
        super(Or, self).__init__(**kwargs)
        self.values = values
        self.schemas = tuple(parse_schema(s) for s in values)

    def _validated(self, data):
        """Validate data if any subschema validates it."""
        errors = []
        for sub in self.schemas:
            try:
                return sub(data)
            except NotValid as ex:
                errors.extend(ex.args)

        raise NotValid(' and '.join(errors))

    def __repr__(self):
        return "<%s>" % (" or ".join(["%r" % (v,) for v in self.values]),)


def nullable(schema, default=UNSPECIFIED):
    """Create a nullable version of schema."""
    return Or(None, schema, default=default)


class And(BaseSchema):

    """Validates if all of the subschemas do."""

    def __init__(self, *values, **kwargs):
        super(And, self).__init__(**kwargs)
        self.values = values
        self.schemas = tuple(parse_schema(s) for s in values)

    def _validated(self, data):
        """Validate data if all subschemas validate it."""
        for sub in self.schemas:
            data = sub(data)
        return data

    def __repr__(self):
        return "<%s>" % (" and ".join(["%r" % (v,) for v in self.values]),)


class Convert(BaseSchema):

    """Convert a value."""

    def __init__(self, converter, **kwargs):
        """Create schema from a conversion function."""
        super(Convert, self).__init__(kwargs)
        self.convert = converter

    def _validated(self, data):
        """Convert data or die trying."""
        try:
            return self.convert(data)
        except (TypeError, ValueError) as ex:
            raise NotValid(*ex.args)

    def __repr__(self):
        """Display schema."""
        return '<Convert: %r>' % (self.convert,)


class Ordered(BaseSchema):

    """Validates an ordered iterable."""

    def __init__(self, schemas, **kwargs):
        """Create schema from an ordered iterable."""
        super(Ordered, self).__init__(**kwargs)
        self._definition = schemas
        self.schemas = type(schemas)(Schema(s) for s in schemas)
        self.length = len(self.schemas)

    def _validated(self, values):
        """Validate if the values are validated one by one in order."""
        if self.length != len(values):
            raise NotValid(
                "%r does not have exactly %d values. (Got %d.)" % (
                    values, self.length, len(values)))
        return type(self.schemas)(
            self.schemas[i].validate(v) for i, v in enumerate(values))

    def __repr__(self):
        """Display schema."""
        return '<Ordered: %r>' % (self.schemas,)
