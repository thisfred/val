lazyval
=======

(Somewhat) functional schema validator, though the lazy applies more to the developer than the implementation.

Inspired by some of the wonderful ideas in schema and flatland: 

https://github.com/halst/schema

http://discorporate.us/projects/flatland/

many of which I outright stole.

The goal is to make validation faster than either, while keeping the very pythonic and minimal style of schema, at the expense of more advanced features.

Current status is: use at your peril, everything subject to change.

I have not optimized much, but for the kind of schemas I need (specifically: to validate JSON that has been loaded into python structures,) I have extremely anecdotal evidence that it's around 10x faster than both schema and flatland. (Again, that is mostly because it does way less, and I intend to keep it that way.)

The schemas understood by lazyval are very similar to the ones in schema, but without the need for a class in case of a one off:

    lazy_schema = {
        'invisible': bool,
        'immutable': bool,
        Optional('favorite_colors'): [str],
        Optional('favorite_foods'): [str],
        'lucky_number': Or(int, None),
        'shoe_size': int,
        'mother': {
            'name': str,
            'nested': {'id': str}},
        Optional('father'): {
            'name': str,
            'nested': {'id': str}}}
    
    result = validate(lazy_schema, some_value)
    # result will be the validated value, or a NotValid exception will be raised.
    result = validates(lazy_schema, some_value)
    # result will be True or False depending on whether some_value was valid for the schema.
    
When the same schema is reused to validate multiple inputs, it can be instantiated with the Schema() class, which will do some preprocessing to make validation faster.

    lazy_schema = Schema({
        'key': int,
        str: object})
    
    result = lazy_schema.validate(some_value)
    # result will be the validated value, or a NotValid exception will be raised.
    result = lazy_schema.validates(some_value)
    # result will be True or False depending on whether some_value was valid for the schema.

Elements that can occur in a schema are: 

  * simple literal values that will match equal values: 
    * `12`, will match `12`
    * `'foo'` will match `'foo'`
  * types that will match anything that is an instance of the type: 
    * `int`, will match `12`
    * `str`, will match `'foo'`
    * `list`, will match `[12, 'foo']`
    * `dict`, will match `{'foo': 12}`
    * `object`, will match any object, so all of the above and more
  * lists of elements that will match list values all of whose elements are validated by one of the elements in the elements in the list: 
    * `[str, int]`, will match `[12, 'foo', 'bar', 'baz', 42]`
    * `['foo', 'bar', 13]`, will match `['foo']` and `['foo', 13]` and `['bar', 'bar', 13, 'bar']`, etc,
  * dictionaries with elements as keys and values, that will match dictionaries all of whose key value pairs are matched by one of the key value pairs in the schema:
    * `{'foo': int, str: int}` will match `{'foo': 83}` and `{'foo': 12, 'bar': 888, 'baz': 299}`, but not `{'foo': 'bar'}` or `{'foo': 21, 12: 'bar'}`
  * `Or(element1, element2, ...)` will match a value that matches any of the elements passed into the Or.
    * `Or('foo', int)` matches `'foo'`, or `12`, or `54`, etc. 
  * `{Optional(simple_literal_key): value}` will match any key value pair that matches `simple_literal_key: value` but the schema will still validate dictionary values with no matching key.
    * `{Optional('foo'): 12}` matches `{'foo': 12}` and `{}` and `{-12.99: 'whatever'}` but not `{'foo': 13}` or `{'foo': 'bar'}`
