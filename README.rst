val
===

A validator for arbitrary Python objects.

Inspired by some of the wonderful ideas in **schema** [1]_ and **flatland**
[2]_ many of which I outright stole.

The goal is to make validation faster than either, while keeping the very
pythonic and minimal style of **schema** [1]_ , at the expense of more
advanced features.

Current status is: used in production code, but only in one place that I know
of.

I have not optimized much, but for the kind of schemas I need (specifically: to
validate JSON that has been loaded into python structures,) I have some
anecdotal evidence that it's around 10x faster than both schema and flatland.
(Again, that is mostly because it does way less.)

The schemas understood by val are very similar to the ones in **schema**
[1]_ , but not 100% compatible::

    >>> from val import Schema, Or, Optional
    >>> schema = Schema({
    ...    'invisible': bool,
    ...    'immutable': bool,
    ...    Optional('favorite_colors'): [basestring],
    ...    Optional('favorite_foods'): [basestring],
    ...    'lucky_number': Or(int, None),
    ...    'shoe_size': int,
    ...    'mother': {
    ...        'name': basestring,
    ...        'nested': {'id': basestring}},
    ...    Optional('father'): {
    ...        'name': basestring,
    ...        'nested': {'id': basestring}}})

    >>> schema.validate(12)
    Traceback (most recent call last): 
        ...
    NotValid: 12 is not of type dict

    >>> schema.validates(12)
    False


Syntax
~~~~~~

Elements that can occur in a schema are: 


Literals
--------

Simple literal values that will match equal values::

    >>> Schema(12).validates(12)
    True
    >>> Schema('foo').validates('foo')
    True


Types
-----

Types that will validate anything that is an instance of the type::

    >>> Schema(int).validates(12)
    True
    >>> Schema(basestring).validates('foo')
    True
    >>> Schema(basestring).validates(u'fnørd')
    True
    >>> Schema(list).validates([12, 'foo'])
    True
    >>> Schema(dict).validates({'foo': 12})
    True
    >>> class Foo(object):
    ...    pass
    >>> foo = Foo()
    >>> Schema(object).validates([foo, (12, 43, 'strawberries'), {}])
    True


Lists
-----

Lists of elements that will validate list values all of whose elements are
validated by one of the elements in the elements in the list (order or
number of elements do not matter, see `Ordered()`)::

    >>> Schema([str, int]).validates([12, 'foo', 'bar', 'baz', 42])
    True
    >>> schema = Schema(['foo', 'bar', 13])
    >>> schema.validates(['foo'])
    True
    >>> schema.validates(['foo', 13])
    True
    >>> schema.validates(['bar', 'bar', 13, 'bar'])
    True


Dictionaries
------------

Dictionaries with elements as keys and values, that will validate
dictionaries all of whose key value pairs are validated by at least one of
the key value pairs in the schema::

    >>> schema = Schema({'foo': int, str: int})
    >>> schema.validates({'foo': 83})
    True
    >>> schema.validates({'foo': 12, 'bar': 888, 'baz': 299})
    True
    >>> schema.validate({'foo': 'bar'}) 
    Traceback (most recent call last): 
        ...
    NotValid: 'foo': 'bar' is not of type <type 'int'>
    >>> schema.validate({'foo': 21, 12: 'bar'})
    Traceback (most recent call last): 
        ...
    NotValid: 12: 'bar' not matched


Callables
---------

Callables (that aren't of type ``type``) will validate any value for which
the callable returns a truthy value. TypeErrors or ValueErrors in the call
will result in a NotValid exception::

    >>> schema = Schema(lambda x: x < 10)
    >>> schema.validates(9)
    True
    >>> schema.validate(10)
    Traceback (most recent call last): 
        ...
    NotValid: 10 not validated by '<lambda>'

To get nicer Exceptions, use functions rather than lambdas::

    >>> def less_than_ten(n):
    ...     """Must be less than 10."""
    ...     return n < 10
    >>> schema = Schema(less_than_ten)
    >>> schema.validates(9)
    True
    >>> schema.validate(10)
    Traceback (most recent call last): 
        ...
    NotValid: 10 not validated by 'Must be less than 10.'


Convert()
---------

``Convert(callable)``, will call the callable on the value being validated,
and substitute the result of that call for the original value in the
validated structure. TypeErrors or ValueErrors in the call will result in a
NotValid exception. This (or supplying a default value to an Optional key)
is the only ways to modify the data being validated during the validation.
Convert is useful to convert between representations (for
instance from timestamps to datetime objects, or uuid string
representations to uuid objects, etc.)::

    >>> from val import Convert
    >>> schema = Schema(Convert(int))
    >>> schema.validate('12')
    12
    >>> schema.validate(42.34)
    42
    >>> schema.validate('foo')
    Traceback (most recent call last): 
        ...
    NotValid: invalid literal for int() with base 10: 'foo'


Or()
----

``Or(element1, element2, ...)`` will validate a value validated by any of the
elements passed into the Or::

    >>> schema = Or('foo', int)
    >>> schema.validates('foo')
    True
    >>> schema.validates(12)
    True
    >>> schema.validate('bar')
    Traceback (most recent call last): 
        ...
    NotValid: 'bar' is not equal to 'foo', 'bar' is not of type <type 'int'>


And()
-----

``And(element1, element2, ...)`` will validate a value validated by all of
the elements passed into the And::

    >>> from val import And
    >>> schema = And(Convert(int), lambda x: x < 12, lambda x: x >= 3)
    >>> schema.validate('3')
    3
    >>> schema.validate(11.6)
    11
    >>> schema.validate('12')
    Traceback (most recent call last): 
        ...
    NotValid: 12 not validated by '<lambda>'
    >>> schema.validate(42.77)
    Traceback (most recent call last): 
        ...
    NotValid: 42 not validated by '<lambda>'
    >>> schema.validate('foo')
    Traceback (most recent call last): 
        ...
    NotValid: invalid literal for int() with base 10: 'foo'


Optional()
----------

``{Optional(simple_literal_key): value}`` will match any key value pair that
matches ``simple_literal_key: value`` but the schema will still validate
dictionary values with no matching key.

``Optional`` can take an optional ``default`` parameter, whose value will be
substituted in the result if the key is not in the data, *or*, when
a ``null_values`` parameter is also specified, if the key has a value that is
one of the null values::

    >>> schema = Schema({
    ...     Optional('foo'): 12})
    >>> schema.validates({'foo': 12})
    True
    >>> schema.validates({})
    True
    >>> schema.validate({'foo': 13})
    Traceback (most recent call last): 
        ...
    NotValid: 'foo': 13 is not equal to 12
    >>> schema.validate({'foo': 'bar'})
    Traceback (most recent call last): 
        ...
    NotValid: 'foo': 'bar' is not equal to 12

    >>> schema = Schema({
    ...    Optional('foo', default=13): int})
    >>> schema.validate({'foo': 12})
    {'foo': 12}
    >>> schema.validate({})
    {'foo': 13}
    >>> schema.validate({'foo': 'bar'})
    Traceback (most recent call last): 
        ...
    NotValid: 'foo': 'bar' is not of type <type 'int'>

    >>> schema = Schema({
    ...     Optional('foo', default=13, null_values=(0, None)): Or(int, None)})
    >>> schema.validate({'foo': 12})
    {'foo': 12}
    >>> schema.validate({'foo': 0})
    {'foo': 13}
    >>> schema.validate({'foo': None})
    {'foo': 13}


Ordered()
---------

``Ordered([element1, element2, element3])`` will validate a list with
**exactly** 3 elements, each of which must be validated by the corresponding
element in the schema. If order and number of elements do not matter, just
use a list::

    >>> from val import Ordered
    >>> schema = Ordered([int, basestring, int, None])
    >>> schema.validates([12, u'fnord', 42, None])
    True
    >>> schema.validate([u'fnord', 42, None, 12])
    Traceback (most recent call last): 
        ...
    NotValid: u'fnord' is not of type <type 'int'>
    >>> schema.validate([12, u'fnord', 42, None, 12])
    Traceback (most recent call last): 
        ...
    NotValid: [12, u'fnord', 42, None, 12] does not have exactly 4 values. (Got 5.)


Parsed schemas
--------------

Other parsed schema objects. So this works::

    >>> sub_schema = Schema({'foo': str, str: int})
    >>> schema = Schema(
    ...     {'key1': sub_schema,
    ...      'key2': sub_schema,
    ...      str: sub_schema})
    >>> schema.validates({
    ...     'key1': {'foo': 'bar'},
    ...     'key2': {'foo': 'qux', 'baz': 43},
    ...     'whatever': {'foo': 'doo', 'fsck': 22, 'tsk': 2992}})
    True


.. [1] https://github.com/halst/schema
.. [2] http://discorporate.us/projects/flatland/
