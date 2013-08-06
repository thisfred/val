class NotValid(Exception):
    pass


class Optional(object):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "<%s>" % (self.value,)


class Or(object):

    def __init__(self, *values):
        self.values = values

    def __str__(self):
        return " or ".join(["<%s>" % (v,) for v in self.values])


def parse_schema(schema):
    return schema


class Schema(object):

    def __init__(self, schema):
        self.schema = parse_schema(schema)


def _dict_item_validate(schema_mandatory, schema_optional, schema_types, key,
                        value):
    if key in schema_mandatory:
        return validate(schema_mandatory[key], value)

    if key in schema_optional:
        return validate(schema_optional[key], value)

    for schema_key, schema_value in schema_types.items():
        if not isinstance(key, schema_key):
            continue
        try:
            return validate(schema_value, value)
        except NotValid:
            continue

    raise NotValid('key %r not matched' % (key,))


def _list_item_validate(schema, value):
    if value in schema:
        return value

    for sub in schema:
        try:
            return validate(sub, value)

        except NotValid:
            pass
    raise NotValid('%r not validated by anything in %s.' % (value, schema))


def validates(schema, data):
    try:
        validate(schema, data)
        return True
    except NotValid:
        return False


def validate(schema, data):

    if isinstance(schema, Or):
        for sub_schema in schema.values:
            try:
                return validate(sub_schema, data)

            except NotValid:
                pass
        raise NotValid('%r not validated by %s' % (data, schema))

    if type(schema) is type:
        if isinstance(data, schema):
            return data

        raise NotValid('%r is not of type %s' % (data, schema))

    if isinstance(schema, dict):
        if not isinstance(data, dict):
            raise NotValid('%r is not of type dict', (data,))
        validated = {}
        not_seen = [
            key for key in schema.keys() if not type(key) is type and not
            isinstance(key, Optional)]
        schema_optional = {}
        schema_mandatory = {}
        schema_types = {}
        for key, value in schema.items():
            if isinstance(key, Optional):
                schema_optional[key.value] = value
                continue

            if type(key) is type:
                schema_types[key] = value
                continue

            schema_mandatory[key] = value
        for key, val in data.items():
            validated[key] = _dict_item_validate(
                schema_mandatory, schema_optional, schema_types, key, val)
            if key in not_seen:
                not_seen.remove(key)
        for key in not_seen:
            if not isinstance(key, Optional):
                raise NotValid('missing key: %s' % (key,))

        return validated

    if type(data) is list:
        return [_list_item_validate(schema, i) for i in data]

    if type(data) is type(schema):
        if data == schema:
            return data

    raise NotValid('%r is not equal to %s' % (data, schema))
