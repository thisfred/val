val
===

.. image:: https://travis-ci.org/thisfred/val.svg?branch=master
    :target: https://travis-ci.org/thisfred/val
.. image:: https://coveralls.io/repos/thisfred/val/badge.svg?branch=master
    :target: https://coveralls.io/r/thisfred/val?branch=master

A validator for arbitrary Python objects. Works with Python 2 and 3.

.. image:: http://thisfred.github.io/val.jpg

Inspired by some of the wonderful ideas in schema_ many of which I outright
stole.

The goal is to make validation faster than it is in schema_, while retaining
its very pythonic and minimal style, at the expense of more advanced features.

The main use case for val is to provide validation of JSON objects at the API
level, and to facilitate writing testable documentation for the benefit of
consumers of that API.


Overview
~~~~~~~~

Schemas in val are objects with at least two methods, ``validates()`` and
``validate()``. A schema is defined in Python code that resembles the structure
of the objects it is meant to validate as closely as possible.

So, if our API expects todo items that have a ``task`` and a `status`` key, its
schema might look like:

.. code:: python

    >>> from val import Schema
    >>> todo_schema = Schema({
    ...     'task': str,
    ...     'status': str})

The ``validates()`` method can be used to determine whether or not an object
satisfies the schema, and returns True if it does, and False if not:

.. code:: python

    >>> todo = {
    ...     'task': 'shave yak',
    ...     'status': 'blocked'}
    >>> todo_schema.validates(todo)
    True
    >>> invalid_todo = {
    ...     'task': 'paint shed',
    ...     'status': 12}
    >>> todo_schema.validates(invalid_todo)
    False

While in some cases this would be sufficient, usually, it's helpful to have
more detailed feedback as to why an object failed to validate. In these cases,
you can use ``validate()``, which returns the validated object if all went well,
and raises a NotValid exception with more details otherwise:

.. code:: python

    >>> validated = todo_schema.validate(todo)  # this works
    >>> valideted = todo_schema.validate(invalid_todo)  # this raises NotValid
    Traceback (most recent call last):
        ...
    val.NotValid: 'status': 12 is not of type <class 'str'>


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

Types and classes will validate anything that is an instance of the type:

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
    ...     pass

    >>> instance = Foo()
    >>> Schema(Foo).validates(instance)
    True

    >>> class SubClass(Foo):
    ...     pass

    >>> subclass_instance = SubClass()
    >>> Schema(Foo).validates(subclass_instance)
    True

    >>> schema = Schema(object)
    >>> all(schema.validates(thing) for thing in [
    ...     instance, (12, 43, 'strawberries'), {}])
    True


Lists
-----

Lists will validate list values all of whose elements are validated by at least
one of the elements in the schema (order or number of elements do not matter,
see `Ordered()`_):

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

A special shortcut exists for a very common pattern where a value is either of
a certain type, or None:

.. code:: python

    >>> from val import nullable
    >>> schema = Schema({'name': nullable(str)})
    >>> schema.validates({'name': 'Grace'})
    True
    >>> schema.validates({'name': None})
    True


Dictionaries
------------

Dictionaries will validate dictionaries all of whose key value pairs are
validated by at least one of the key value pairs in the schema, and that are
not missing any of the keys specified (unless they are specified as
`Optional()`_):

.. code:: python

    >>> schema = Schema({'foo': int, str: int})
    >>> schema.validates({'foo': 83})
    True

    >>> schema.validates({'foo': 12, 'bar': 888, 'baz': 299})
    True

    >>> schema.validate({'foo': 'bar'})
    Traceback (most recent call last):
        ...
    val.NotValid: 'foo': 'bar' is not of type <class 'int'>

    >>> schema.validate({'qux': 19})
    Traceback (most recent call last):
        ...
    val.NotValid: missing key: 'foo'

    >>> schema.validate({'foo': 21, 12: 'bar'})
    Traceback (most recent call last):
        ...
    val.NotValid: 12: 'bar' not matched


Callables
---------

Callables (that aren't of type ``type``) will validate any value for which the
callable returns a truthy value. TypeErrors or ValueErrors in the call will
result in a NotValid exception:

.. code:: python

    >>> schema = Schema(lambda x: x < 10)
    >>> schema.validates(9)
    True

    >>> schema.validate(10)
    Traceback (most recent call last):
        ...
    val.NotValid: 10 invalidated by '<lambda>'

To get nicer error messages, use functions rather than lambdas (if the function
has a doc string it will be used in the error message, otherwise the name of
the funtion will):

.. code:: python

    >>> def less_than_ten(n):
    ...     """Must be less than 10."""
    ...     return n < 10

    >>> schema = Schema(less_than_ten)
    >>> schema.validates(9)
    True

    >>> schema.validate(10)
    Traceback (most recent call last):
        ...
    val.NotValid: 10 invalidated by 'Must be less than 10.'


Convert()
---------

``Convert(callable)`` will call the callable on the value being validated,
and substitute the result of that call for the original value in the
validated structure. TypeErrors or ValueErrors in the call will result in a
NotValid exception. This or supplying `Default Values`_ are the only ways to
modify the data during validation. For that reason it should be used sparingly.

Convert is useful to convert between representations (for instance from
timestamps to datetime objects, or uuid string representations to uuid objects,
etc.):

.. code:: python

    >>> from val import Convert
    >>> schema = Schema(Convert(int))
    >>> schema.validate('12')
    12

    >>> schema.validate(42.34)
    42

    >>> schema.validate('foo')
    Traceback (most recent call last):
        ...
    val.NotValid: invalid literal for int() with base 10: 'foo'


Or()
----

``Or(element1, element2, ...)`` will validate a value validated by any of the
elements passed into the Or:

.. code:: python

    >>> from val import Or
    >>> schema = Or('foo', int)
    >>> schema.validates('foo')
    True

    >>> schema.validates(12)
    True

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

    >>> schema.validate('12')
    Traceback (most recent call last):
        ...
    val.NotValid: 12 invalidated by '<lambda>'

    >>> schema.validate(42.77)
    Traceback (most recent call last):
        ...
    val.NotValid: 42 invalidated by '<lambda>'

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

    >>> from val import Optional
    >>> schema = Schema({Optional('foo'): 12})
    >>> schema.validates({'foo': 12})
    True

    >>> schema.validates({})
    True

    >>> schema.validate({'foo': 13})
    Traceback (most recent call last):
        ...
    val.NotValid: 'foo': 13 is not equal to 12

    >>> schema.validate({'foo': 'bar'})
    Traceback (most recent call last):
        ...
    val.NotValid: 'foo': 'bar' is not equal to 12


Ordered()
---------

``Ordered([element1, element2, element3])`` will validate a list with
**exactly** 3 elements, each of which must be validated by the corresponding
element in the schema. If order and number of elements do not matter, just
use `Lists`_:

.. code:: python

    >>> from val import Ordered
    >>> schema = Ordered([int, str, int, None])
    >>> schema.validates([12, 'fnord', 42, None])
    True

    >>> schema.validate(['fnord', 42, None, 12])
    Traceback (most recent call last):
        ...
    val.NotValid: 'fnord' is not of type <class 'int'>

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


FAQ
~~~


How do I validate only some of the keys in a dictionary?
--------------------------------------------------------

Often when validating input there will be values present that your code doesn't
act upon, and doesn't care about the presence or absence of. You can make your
schema similarly indifferent by adding ``str: object`` (assuming the keys in
the dictionary are all strings, like they are when your data comes from JSON.
If even the type of the keys is variable, you can use ``object: object``.) This
will match and validate any keys in the dictionary that you didn't explicitly
specify.

.. code:: python

    >>> schema = Schema({
    ...     'username': str,
    ...     'password': str,
    ...     str: object})

    >>> schema.validates({
    ...     'username': 'bob',
    ...     'password': 'hella rancid hazelnuts',
    ...     'shopping_cart': {
    ...         'contents': ['Meet the Parens: A Lisp primer.']}})
    True

    >>> schema.validate({
    ...     'username': 'connie',
    ...     'goldfish': 12})
    Traceback (most recent call last):
         ...
    val.NotValid: missing key: 'password'


Advanced Topics
~~~~~~~~~~~~~~~


Default Values
--------------

One can supply a default value to any (subclass of) Schema, which will be used
in place of the validated value if that value was ``None``.

.. code:: python

    >>> schema = Schema(Or(str, None), default='default value')
    >>> schema.validate('supplied value')
    'supplied value'

    >>> schema.validate('')
    ''

    >>> schema.validate(None)
    'default value'


Default values will also work for dictionary keys that are specified as
``Optional``:

.. code:: python

    >>> schema = Schema(
    ...     {'foo': str,
    ...      Optional('bar'): Or(int, None, default=23)})

    >>> schema.validate({'foo': 'yes'}) == {'bar': 23, 'foo': 'yes'}
    True


Additional Validators
---------------------

Sometimes it is useful to do validation that depends on multiple parts of the
data at once. For this purpose, Schemas can be initialized with additional
validators.


.. code:: python

    >>> def maximum_total(value):
    ...     """The total sum must not exceed 500."""
    ...     return sum(value.values()) <= 500

    >>> schema = Schema({str: int}, additional_validators=(maximum_total,))
    >>> schema.validates({'foo': 12, 'bar': 400})
    True

    >>> schema.validate({'foo': 250, 'bar': 251})
    Traceback (most recent call last):
         ...
    val.NotValid: ... invalidated by 'The total sum must not exceed 500.'


Serializing Schemas
-------------------

When your application receives JSON from clients, it can be useful to define
explicit schemas that those clients have to abide by. Pointing to source code 
isn't an especially great way to communicate to other developers what is or
isn't considered valid JSON by your application, especially if they aren't 
developing in Python. For this purpose, teleport_, a lightweight JSON format to
describe schemas, is better suited.

A subset of valid val schemas is serializable/exportable to teleport_. 
Note that things like default values and additional validators will be lost
when serializing to teleport, because it has no way to express them.

Combining doctests with this serialization provides a way to specify what your
application considers valid, and verify in your tests that you didn't
unintentionally break clients' assumptions.

If your code contains the following schema for todo items:

.. code:: python

    >>> todo = Schema({
    ...     "task": str,
    ...     Optional("priority"): int,
    ...     Optional("status"): str})

Then in your API documentation you could use the ``document()`` helper and
have doctests verify the output, as is the case here.

.. code:: python

    >>> from val import tp
    >>> print(tp.document(todo))
    {
      "Struct": {
        "optional": {
          "priority": "Integer",
          "status": "String"
        },
        "required": {
          "task": "String"
        }
      }
    }


.. _schema: https://github.com/halst/schema
.. _teleport: http://www.teleport-json.org/
