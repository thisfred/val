import os
import errno
import json
import pytest
import val
from val import NotValid
from val.json_schema import parse_json_schema
import requests


class MockResponse(object):

    def __init__(self, content):
        self.content = content


def cached_get(url):
    path = url.split(':')[1].split('/')
    filename = os.path.join(
        os.path.dirname(val.__file__), os.path.pardir, 'tests', *path)
    dirname = os.path.join(
        os.path.dirname(val.__file__), os.path.pardir, 'tests', *path[:-1])
    if os.path.exists(filename):
        mock = object()
        with open(filename, 'r') as content:
            mock = MockResponse(content.read())
        return mock
    result = _orig_get(url)
    try:
        os.makedirs(dirname)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(dirname):
            pass
        else:
            raise
    with open(filename, 'w') as content:
        content.write(result.content)
    return result

_orig_get = requests.get
requests.get = cached_get

json_tests_file = os.path.join(
    os.path.dirname(val.__file__), os.path.pardir, 'tests', 'draft4.json')
with open(json_tests_file, 'r') as draft4:
    JSON_TESTS = json.loads(draft4.read())


@pytest.mark.parametrize('json_test', JSON_TESTS)
def test_json(json_test):
    data = json_test['data']
    schema = parse_json_schema(json_test['schema'])
    if json_test['valid']:
        assert schema.validate(data) == data
    else:
        with pytest.raises(NotValid):
            schema.validate(data)
