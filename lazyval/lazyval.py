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


def _dict_item_validate(schema_optional, schema_types, key, value):
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


def _schema_list_item_validate(sub_schemas, value):
    for sub in sub_schemas:
        try:
            return sub(value)

        except NotValid:
            pass

    raise NotValid('%r not validated by anything in %s.' % (
        value, sub_schemas))


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
        optional = {}
        mandatory = {}
        types = {}
        for key, value in schema.items():
            if isinstance(key, Optional):
                optional[key.value] = value
                continue

            if type(key) is type:
                types[key] = value
                continue

            mandatory[key] = value
        to_validate = data.keys()
        for key, sub_schema in mandatory.items():
            if key not in data:
                raise NotValid('missing key: %s' % (key,))
            validated[key] = validate(sub_schema, data[key])
            to_validate.remove(key)
        for key in to_validate:
            validated[key] = _dict_item_validate(
                optional, types, key, data[key])

        return validated

    if type(data) is list:
        if not isinstance(data, list):
            raise NotValid('%r is not of type list', (data,))

        return [_list_item_validate(schema, i) for i in data]

    if data == schema:
        return data

    raise NotValid('%r is not equal to %s' % (data, schema))


def parse_schema(schema):
    if isinstance(schema, Or):
        sub_schemas = [parse_schema(v) for v in schema.values]

        def or_validator(data):
            for schema in sub_schemas:
                try:
                    return schema(data)
                except NotValid:
                    pass
            raise NotValid('%r not validated by %s' % (data, schema))

        return or_validator

    if type(schema) is type:

        def type_validator(data):
            if isinstance(data, schema):
                return data

            raise NotValid('%r is not of type %s' % (data, schema))

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
                    raise NotValid('missing key: %s' % (key,))
                validated[key] = sub_schema(data[key])
                to_validate.remove(key)
            for key in to_validate[:]:
                value = data[key]
                if key in optional:
                    validated[key] = optional[key](value)
                    to_validate.remove(key)
                    continue
                for key_schema, value_schema in types.items():
                    if not isinstance(key, key_schema):
                        continue
                    try:
                        validated[key] = value_schema(value)
                    except NotValid:
                        continue
                    else:
                        to_validate.remove(key)
                        break
                else:
                    raise NotValid('key %r not matched' % (key,))

            if to_validate:
                raise NotValid('keys %s not matched' % (to_validate,))
            return validated

        return dict_validator

    if isinstance(schema, list):

        sub_schemas = [parse_schema(s) for s in schema]

        def list_validator(data):
            if not isinstance(data, list):
                raise NotValid('%r is not of type list', (data,))

            return [
                _schema_list_item_validate(sub_schemas, value)
                for value in data]

        return list_validator

    def static_validator(data):
        if data == schema:
            return data

        raise NotValid('%r is not equal to %s' % (data, schema))

    return static_validator


class Schema(object):

    def __init__(self, schema):
        self.schema = parse_schema(schema)

    def validate(self, data):
        return self.schema(data)

    def validates(self, data):
        try:
            self.schema(data)
            return True
        except NotValid:
            return False
