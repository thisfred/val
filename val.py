"""
Copyright (c) 2013
Eric Casteleijn, <thisfred@gmail.com>
"""

__version__ = '0.4.0'

NOT_SUPPLIED = object()


class NotValid(Exception):
    pass


def get_repr(thing):
    return (
        getattr(thing, 'func_doc') or
        getattr(thing, 'func_name') or
        repr(thing))


def parse_schema(schema):
    if isinstance(schema, Schema):
        return schema.validate

    if type(schema) is type:

        def type_validator(data):
            if isinstance(data, schema):
                return data

            raise NotValid('%r is not of type %r' % (data, schema))

        return type_validator

    if isinstance(schema, dict):

        optional = {}
        defaults = {}
        mandatory = {}
        types = {}
        for key, value in schema.items():
            if isinstance(key, Optional):
                optional[key.value] = parse_schema(value)
                if key.default is not NOT_SUPPLIED:
                    defaults[key.value] = (key.default, key.null_values)
                continue

            if type(key) is type:
                types[key] = parse_schema(value)
                continue

            mandatory[key] = parse_schema(value)

        def dict_validator(data):
            missing = defaults.keys()
            if not isinstance(data, dict):
                raise NotValid('%r is not of type dict' % (data,))
            validated = {}
            to_validate = data.keys()
            for key, sub_schema in mandatory.items():
                if key not in data:
                    raise NotValid('missing key: %r' % (key,))
                try:
                    validated[key] = sub_schema(data[key])
                except NotValid, e:
                    raise NotValid('%s: %s' % (key, e.args))
                to_validate.remove(key)
            for key in to_validate:
                value = data[key]
                if key in optional:
                    try:
                        validated[key] = optional[key](value)
                    except NotValid, e:
                        raise NotValid('%s: %s' % (key, e.args))
                    if key in missing:
                        _, null_values = defaults[key]
                        if null_values is not NOT_SUPPLIED:
                            if validated[key] in null_values:
                                continue
                        missing.remove(key)
                    continue  # pragma: nocover
                for key_schema, value_schema in types.items():
                    if not isinstance(key, key_schema):
                        continue
                    try:
                        validated[key] = value_schema(value)
                    except NotValid:
                        continue
                    else:
                        break
                else:
                    raise NotValid('key %r and value %s not matched' % (
                        key, value))
            for key in missing:
                validated[key] = defaults[key][0]
            return validated

        return dict_validator

    if type(schema) in (list, tuple, set):

        sub_schemas = [parse_schema(s) for s in schema]

        def item_validator(value):
            for sub in sub_schemas:
                try:
                    return sub(value)

                except NotValid:
                    pass

            raise NotValid('%r not validated by anything in %s.' % (
                value, schema))

        def collection_validator(data):
            if not type(data) is type(schema):
                raise NotValid('%r is not of type %s' % (data, type(schema)))

            return type(schema)(item_validator(value) for value in data)

        return collection_validator

    if callable(schema):

        def callable_validator(data):
            try:
                if schema(data):
                    return data
                else:
                    raise NotValid(
                        "%r not validated by '%s'" % (data, get_repr(schema)))
            except (TypeError, ValueError), e:
                raise NotValid(*e.args)

        return callable_validator

    def static_validator(data):
        if data == schema:
            return data

        raise NotValid('%r is not equal to %r' % (data, schema))

    return static_validator


class Schema(object):

    def __init__(self, schema, additional_validators=None):
        self._orig_schema = schema
        self.schema = parse_schema(schema)
        self.additional_validators = additional_validators or []

    def __repr__(self):
        return repr(self._orig_schema)

    def validate(self, data):
        validated = self.schema(data)
        for validator in self.additional_validators:
            if not validator(validated):
                raise NotValid(
                    "%s not validated by additional validator '%s'" % (
                        validated, get_repr(validator)))
        return validated

    def validates(self, data):
        try:
            self.validate(data)
            return True
        except NotValid:
            return False


class Optional(object):

    def __init__(self, value, default=NOT_SUPPLIED, null_values=NOT_SUPPLIED):
        self.value = value
        self.default = default
        self.null_values = null_values

    def __repr__(self):
        return "<Optional: %r>" % (self.value,)


class Or(Schema):

    def __init__(self, *values):
        self.values = values
        self.schemas = tuple(parse_schema(s) for s in values)

    def validate(self, data):
        errors = []
        for sub in self.schemas:
            try:
                return sub(data)
            except NotValid, e:
                errors.extend(e.args)
        raise NotValid(*errors)

    def __repr__(self):
        return "<%s>" % (" or ".join(["%r" % (v,) for v in self.values]),)


class And(Schema):

    def __init__(self, *values):
        self.values = values
        self.schemas = tuple(parse_schema(s) for s in values)

    def validate(self, data):
        for sub in self.schemas:
            data = sub(data)
        return data

    def __repr__(self):
        return "<%s>" % (" and ".join(["%r" % (v,) for v in self.values]),)


class Convert(Schema):

    def __init__(self, conversion):
        self.convert = conversion

    def validate(self, data):
        try:
            return self.convert(data)
        except (TypeError, ValueError), e:
            raise NotValid(*e.args)

    def __repr__(self):
        return '<Convert: %r>' % (self.convert,)


class Ordered(Schema):

    def __init__(self, schemas):
        self._orig_schema = schemas
        self.schemas = type(schemas)(Schema(s) for s in schemas)
        self.length = len(self.schemas)

    def validate(self, values):
        if self.length != len(values):
            raise NotValid(
                "Does not have exactly %d values. (Got %d.)" % (
                    self.length, len(values)))
        return type(self.schemas)(
            self.schemas[i].validate(v) for i, v in enumerate(values))

    def __repr__(self):
        return '<Ordered: %r>' % (self.schemas,)
