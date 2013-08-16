val
===
![val](http://smartassradio.com/wp-content/gallery/site-images/fat-val-kilmer.jpg)

A validator for arbitrary Python objects.

Inspired by some of the wonderful ideas in schema and flatland: 

https://github.com/halst/schema

http://discorporate.us/projects/flatland/

many of which I outright stole.

The goal is to make validation faster than either, while keeping the very
pythonic and minimal style of schema, at the expense of more advanced features.

One of the shortcuts I took is bailing out on the first encountered validation
error. The rationale (or rationalization, if you must) is that the library is
meant to validate API inputs, rather than direct user input, so the burden is
somewhat shifted to the client side to send valid requests. I do not suggest
using val for validating web form input.

Current status is: moving towards 0.1 release, somewhat stable, somewhat
complete.

I have not optimized much, but for the kind of schemas I need (specifically: to
validate JSON that has been loaded into python structures,) I have extremely
anecdotal evidence that it's around 10x faster than both schema and flatland.
(Again, that is mostly because it does way less, and I intend to keep it that
way.)

The schemas understood by lazyval are very similar to the ones in schema:
    from val import Schema, Or
    
    schema = Schema({
        'invisible': bool,
        'immutable': bool,
        Optional('favorite_colors'): [basestring],
        Optional('favorite_foods'): [basestring],
        'lucky_number': Or(int, None),
        'shoe_size': int,
        'mother': {
            'name': basestring,
            'nested': {'id': basestring}},
        Optional('father'): {
            'name': basestring,
            'nested': {'id': basestring}}})
    
    result = schema.validate(some_value)
    # result will be the validated value, or a NotValid exception will be
    # raised.

    result = schema.validates(some_value)
    # result will be True or False depending on whether some_value was valid
    # for the schema.

Elements that can occur in a schema are: 

  * simple literal values that will match equal values: 
    * `12`, will validate `12`
    * `'foo'` will validate `'foo'`
  * types that will validate anything that is an instance of the type: 
    * `int`, will validate `12`
    * `basestring`, will validate `'foo'` and `u'fnørd'`
    * `list`, will validate `[12, 'foo']`
    * `dict`, will validate `{'foo': 12}`
    * `object`, will validate any object, so all of the above and more
  * lists of elements that will validate list values all of whose elements are
    validated by one of the elements in the elements in the list (order or
    number of elements do not matter, see Ordered): 
    * `[str, int]`, will validate `[12, 'foo', 'bar', 'baz', 42]`
    * `['foo', 'bar', 13]`, will validate `['foo']` and `['foo', 13]` and
      `['bar', 'bar', 13, 'bar']`, etc,
  * dictionaries with elements as keys and values, that will validate
    dictionaries all of whose key value pairs are validated by at least one of
    the key value pairs in the schema:
    * `{'foo': int, str: int}` will match `{'foo': 83}` and
      `{'foo': 12, 'bar': 888, 'baz': 299}`, but not `{'foo': 'bar'}` or
      `{'foo': 21, 12: 'bar'}`
  * callables (that aren't of type `type`) will validate any value for which
    the callable returns a truthy value. TypeErrors or ValueErrors in the call
    will result in a NotValid exception.
    * `lambda x: x < 10` will validate `9` but not `10`, etc.
  * `Convert(callable)`, will call the callable on the value being validated,
    and substitute the result of that call for the original value in the
    validated structure. TypeErrors or ValueErrors in the call will result in a
    NotValid exception. This is the only element that will change the data
    being validated. It's useful to convert between representations (for
    instance from timestamps to datetime objects, or uuid string
    representations to uuid objects, etc.)
    * `Convert(int)` will validate `'12'` and put `12` in the result, or
      `42.34` and put `42` in the result, but it will not validate `'foo'`.  
  * `Or(element1, element2, ...)` will validate a value validated by any of the
    elements passed into the Or.
    * `Or('foo', int)` matches `'foo'`, or `12`, or `54`, etc. 
  * `And(element1, element2, ...)` will validate a value validated by all of
    the elements passed into the And.
    * `And(Convert(int), lambda x: x < 12, lambda x: x >= 3)` will validate
      `'3'` and return `3` or `11.6` and return `11`, but not `'12'`, `42.77`,
      or `'foo'` 
  * `{Optional(simple_literal_key): value}` will match any key value pair that
    matches `simple_literal_key: value` but the schema will still validate
    dictionary values with no matching key.
    * `{Optional('foo'): 12}` matches `{'foo': 12}` and `{}` but not
      `{'foo': 13}` or `{'foo': 'bar'}`
  * `Ordered([element1, element2, element3]) will validate a list with
    *exactly* 3 elements, each of which must be validated by the corresponding
    element in the schema. If order and number of elements do not matter, just
    use a list.
  * Other parsed schema objects. So this works:

        sub_schema = Schema({'foo': str, str: int})
        schema = Schema(
            {'key1': sub_schema,
             'key2': sub_schema,
             str: sub_schema})
        schema.validate(
            {'key1': {'foo': 'bar'},
             'key2': {'foo': 'qux', 'baz': 43},
             'whatever': {'foo': 'doo', 'fsck': 22, 'tsk': 2992}}))
