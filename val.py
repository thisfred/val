"""
Copyright (c) 2013
Eric Casteleijn, <thisfred@gmail.com>
"""

__version__ = '0.1.1'


class NotValid(Exception):
    pass


class Optional(object):

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return "<Optional: %r>" % (self.value,)


class Or(object):

    def __init__(self, *values):
        self.values = values

    def __repr__(self):
        return "<%s>" % (" or ".join(["%r" % (v,) for v in self.values]),)


class And(object):

    def __init__(self, *values):
        self.values = values

    def __repr__(self):
        return "<%s>" % (" and ".join(["%r" % (v,) for v in self.values]),)


class Convert(object):

    def __init__(self, conversion):
        self.convert = conversion

    def __repr__(self):
        return '<Convert: %r>' % (self.convert,)


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
        mandatory = {}
        types = {}
        for key, value in schema.items():
            if isinstance(key, Optional):
                optional[key.value] = parse_schema(value)
                continue

            if type(key) is type:
                types[key] = parse_schema(value)
                continue

            mandatory[key] = parse_schema(value)

        def dict_validator(data):
            if not isinstance(data, dict):
                raise NotValid('%r is not of type dict', (data,))
            validated = {}
            to_validate = data.keys()
            for key, sub_schema in mandatory.items():
                if key not in data:
                    raise NotValid('missing key: %r' % (key,))
                validated[key] = sub_schema(data[key])
                to_validate.remove(key)
            for key in to_validate:
                value = data[key]
                if key in optional:
                    validated[key] = optional[key](value)
                    continue
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
                    raise NotValid('key %r not matched' % (key,))

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
                raise NotValid('%r is not of type %s', (data, type(schema)))

            return type(schema)(item_validator(value) for value in data)

        return collection_validator

    if callable(schema):

        def callable_validator(data):
            try:
                if schema(data):
                    return data
                else:
                    raise NotValid('%r does not satisfy %r' % (data, schema))
            except (TypeError, ValueError), e:
                raise NotValid(e)

        return callable_validator

    if isinstance(schema, And):
        sub_schemas = [parse_schema(v) for v in schema.values]

        def and_validator(data):
            for sub in sub_schemas:
                data = sub(data)
            return data

        return and_validator

    if isinstance(schema, Or):
        sub_schemas = [parse_schema(v) for v in schema.values]

        def or_validator(data):
            for sub in sub_schemas:
                try:
                    return sub(data)
                except NotValid:
                    pass
            raise NotValid('%r not validated by %r' % (data, schema))

        return or_validator

    if isinstance(schema, Convert):

        def conversion_validator(data):
            try:
                return schema.convert(data)
            except (TypeError, ValueError), e:
                raise NotValid(e)

        return conversion_validator

    def static_validator(data):
        if data == schema:
            return data

        raise NotValid('%r is not equal to %r' % (data, schema))

    return static_validator


class Schema(object):

    def __init__(self, schema):
        self._orig_schema = schema
        self.schema = parse_schema(schema)

    def __repr__(self):
        return repr(self._orig_schema)

    def validate(self, data):
        return self.schema(data)

    def validates(self, data):
        try:
            self.schema(data)
            return True
        except NotValid:
            return False
