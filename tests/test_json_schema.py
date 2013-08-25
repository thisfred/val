import os
import json
import pytest
import val
from val import NotValid
from val.json_schema import parse_json_schema

json_tests_file = os.path.join(
    os.path.dirname(val.__file__), os.path.pardir, 'tests', 'draft4.json')
print json_tests_file
with open(json_tests_file, 'r') as draft4:
    JSON_TESTS = json.loads(draft4.read())


@pytest.mark.parametrize('json_test', JSON_TESTS)
def test_json(json_test):
    schema = parse_json_schema(json_test['schema'])
    data = json_test['data']
    if json_test['valid']:
        assert schema.validate(data) == data
    else:
        with pytest.raises(NotValid):
            schema.validate(data)
