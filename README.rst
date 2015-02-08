val
===

.. image:: https://travis-ci.org/thisfred/val.svg?branch=master
    :target: https://travis-ci.org/thisfred/val
.. image:: https://coveralls.io/repos/thisfred/val/badge.svg?branch=master
    :target: https://coveralls.io/r/thisfred/val?branch=master

A validator for arbitrary Python objects. Works with Python 2 and 3.

.. image:: http://thisfred.github.io/val.jpg

Inspired by some of the wonderful ideas in schema_ and flatland_, many of which
I outright stole.

The goal is to make validation faster than either, while keeping the very
pythonic and minimal style of schema_ , at the expense of more advanced
features.

Current status is: used in production code, but only in one place that I know
of.

I have not optimized much, but for the kind of schemas I need (specifically: to
validate JSON that has been loaded into python structures as part of a REST API,)
I have some anecdotal evidence that it's around ten times faster than both schema
and flatland. (Again, that is mostly because it does way less.)

The schemas understood by val are very similar to the ones in schema_ , but not
100% compatible:

.. code:: python

    >>> from val import Schema, Or, Optional
    >>> schema = Schema({
    ...    'invisible': bool,
    ...    'immutable': bool,
    ...    Optional('favorite_colors'): [str],
    ...    Optional('favorite_foods'): [str],
    ...    'lucky_number': Or(int, None),
    ...    'shoe_size': int,
    ...    'mother': {
    ...        'name': str,
    ...        'nested': {'id': str}},
    ...    Optional('father'): {
    ...        'name': str,
    ...        'nested': {'id': str}}})


.. note::

    The doctests will only work under Python 3, but for fairly trivial reasons.
    All other tests are run against current versions of both Python 2 and 3, 
    and cover 100% of the code, so you should feel safe to use this with
    either.


Syntax
~~~~~~

Elements that can occur in a schema are: 


Literals
--------

Simple literal values will match equal values:

.. code:: python

    >>> Schema(12).validates(12)
    True
    >>> Schema('foo').validates('foo')
    True


Types
-----

Types will validate anything that is an instance of the type:

.. code:: python

    >>> Schema(int).validates(12)
    True
    >>> Schema(str).validates('foo')
    True
    >>> Schema(str).validates('fnørd')
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

Lists will validate list values all of whose elements are
validated by at least one of the elements in the schema (order or
number of elements do not matter, see `Ordered()`_):

.. code:: python

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

Dictionaries will validate dictionaries all of whose key value
pairs are validated by at least one of the key value pairs in 
the schema:

.. code:: python

    >>> schema = Schema({'foo': int, str: int})
    >>> schema.validates({'foo': 83})
    True
    >>> schema.validates({'foo': 12, 'bar': 888, 'baz': 299})
    True
    >>> schema.validates({'foo': 'bar'}) 
    False

    >>> schema.validate({'foo': 'bar'}) 
    Traceback (most recent call last): 
         ...
    val.NotValid: 'foo': 'bar' is not of type <class 'int'>

    >>> schema.validates({'foo': 21, 12: 'bar'})
    False

    >>> schema.validate({'foo': 21, 12: 'bar'})
    Traceback (most recent call last): 
       ...
    val.NotValid: 12: 'bar' not matched


Callables
---------

Callables (that aren't of type ``type``) will validate any value for which
the callable returns a truthy value. TypeErrors or ValueErrors in the call
will result in a NotValid exception:

.. code:: python

    >>> schema = Schema(lambda x: x < 10)
    >>> schema.validates(9)
    True
    >>> schema.validates(10)
    False

    >>> schema.validate(10)
    Traceback (most recent call last): 
        ...
    val.NotValid: 10 not validated by '<lambda>'

To get nicer Exceptions, use functions rather than lambdas:

.. code:: python

    >>> def less_than_ten(n):
    ...     """Must be less than 10."""
    ...     return n < 10
    >>> schema = Schema(less_than_ten)
    >>> schema.validates(9)
    True
    >>> schema.validates(10)
    False

    >>> schema.validate(10)
    Traceback (most recent call last): 
        ...
    val.NotValid: 10 not validated by 'Must be less than 10.'


Convert()
---------

``Convert(callable)`` will call the callable on the value being validated,
and substitute the result of that call for the original value in the
validated structure. TypeErrors or ValueErrors in the call will result in a
NotValid exception. This or supplying a default value are the only ways to
modify the data being validated during the validation.
Convert is useful to convert between representations (for
instance from timestamps to datetime objects, or uuid string
representations to uuid objects, etc.):

.. code:: python

    >>> from val import Convert
    >>> schema = Schema(Convert(int))
    >>> schema.validate('12')
    12
    >>> schema.validate(42.34)
    42
    >>> schema.validates('foo')
    False

    >>> schema.validate('foo')
    Traceback (most recent call last): 
        ...
    val.NotValid: invalid literal for int() with base 10: 'foo'


Or()
----

``Or(element1, element2, ...)`` will validate a value validated by any of the
elements passed into the Or:

.. code:: python

    >>> schema = Or('foo', int)
    >>> schema.validates('foo')
    True
    >>> schema.validates(12)
    True
    >>> schema.validates('bar')
    False

    >>> schema.validate('bar')
    Traceback (most recent call last): 
        ...
    val.NotValid: 'bar' is not equal to 'foo', 'bar' is not of type <class 'int'>


And()
-----

``And(element1, element2, ...)`` will validate a value validated by all of
the elements passed into the And:

.. code:: python

    >>> from val import And
    >>> schema = And(Convert(int), lambda x: x < 12, lambda x: x >= 3)
    >>> schema.validate('3')
    3
    >>> schema.validate(11.6)
    11
    >>> schema.validates('12')
    False

    >>> schema.validate('12')
    Traceback (most recent call last): 
        ...
    val.NotValid: 12 not validated by '<lambda>'

    >>> schema.validates(42.77)
    False

    >>> schema.validate(42.77)
    Traceback (most recent call last): 
        ...
    val.NotValid: 42 not validated by '<lambda>'

    >>> schema.validates('foo')
    False

    >>> schema.validate('foo')
    Traceback (most recent call last): 
        ...
    val.NotValid: invalid literal for int() with base 10: 'foo'


Optional()
----------

``{Optional(simple_literal_key): value}`` will match any key value pair that
matches ``simple_literal_key: value`` but the schema will still validate
dictionary values with no matching key.


.. code:: python

    >>> schema = Schema({
    ...     Optional('foo'): 12})
    >>> schema.validates({'foo': 12})
    True
    >>> schema.validates({})
    True
    >>> schema.validates({'foo': 13})
    False

    >>> schema.validate({'foo': 13})
    Traceback (most recent call last): 
        ...
    val.NotValid: 'foo': 13 is not equal to 12

    >>> schema.validates({'foo': 'bar'})
    False

    >>> schema.validate({'foo': 'bar'})
    Traceback (most recent call last): 
        ...
    val.NotValid: 'foo': 'bar' is not equal to 12


Ordered()
---------

``Ordered([element1, element2, element3])`` will validate a list with
**exactly** 3 elements, each of which must be validated by the corresponding
element in the schema. If order and number of elements do not matter, just
use a list:

.. code:: python

    >>> from val import Ordered
    >>> schema = Ordered([int, str, int, None])
    >>> schema.validates([12, 'fnord', 42, None])
    True
    >>> schema.validates(['fnord', 42, None, 12])
    False

    >>> schema.validate(['fnord', 42, None, 12])
    Traceback (most recent call last):
        ...
    val.NotValid: 'fnord' is not of type <class 'int'>
    >>> schema.validates([12, 'fnord', 42, None, 12])
    False

    >>> schema.validate([12, 'fnord', 42, None, 12])
    Traceback (most recent call last):
        ...
    val.NotValid: [12, 'fnord', 42, None, 12] does not have exactly 4 values. (Got 5.)


Parsed Schemas
--------------

Other parsed schema objects. So this works:

.. code:: python

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


Default Values
--------------

One can supply a default value to any (subclass of) Schema, which will be used
in place of the validated value if that evaluates to `False`.

.. code:: python

    >>> schema = Schema(str, default='default value')
    >>> schema.validate('supplied value')
    'supplied value'
    >>> schema.validate('')
    'default value'

Note that the original value must still be valid for the schema, so this will
not work:

.. code:: python

    >>> schema.validates(None)
    False

But this will:

.. code:: python

    >>> schema = Or(str, None, default='default value')
    >>> schema.validate(None)
    'default value'

Default values will also work for dictionary keys that are specified as
`Optional`:

.. code:: python

    >>> schema = Schema(
    ...     {'foo': str,
    ...      Optional('bar'): Or(int, None, default=23)})
    >>> schema.validate({'foo': 'yes'}) == {'bar': 23, 'foo': 'yes'}
    True

.. _schema: https://github.com/halst/schema
.. _flatland: http://discorporate.us/projects/flatland/
