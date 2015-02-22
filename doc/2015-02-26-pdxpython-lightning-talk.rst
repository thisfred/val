:title: Validating JSON in your APIs
:author: Eric Casteleijn
:description: Using val to validate JSON objects in your APIs.
:css: presentation.css

----

Validating JSON in your APIs
============================


<http://github.com/thisfred/val>


Eric Casteleijn

thisfred@gmail.com | ericc@simple.com | @thisfred

----

Schemas should
--------------

be brief, readable, pythonic, and resemble the data they validate\ [#]_.

.. code:: python

    >>> from val import Schema

    >>> todo_schema = Schema({
    ...     'task': str,
    ...     'status': str})

    >>> todo = {
    ...     'task': 'shave yak',
    ...     'status': 'blocked'}

    >>> todo_schema.validates(todo)
    True

.. [#] These ideas mostly stolen from <https://github.com/halst/schema>


----

give meaningful feedback for invalid data.

.. code:: python

    >>> todo_schema = Schema({
    ...     'task': str,
    ...     'status': str})

    >>> todo_schema.validate({'task': 'shave yak'})
    Traceback (most recent call last):
        ...
    val.NotValid: missing key: 'status'

    >>> todo_schema.validate(12)
    Traceback (most recent call last):
        ...
    val.NotValid: 12 is not of type dict

----

help test and document server and client code\ [#]_.

.. code:: python

    >>> todo_schema = Schema({
    ...     'task': str,
    ...     'status': str})

    >>> from val import tp

    >>> print(tp.document(todo_schema))
    {
      "Struct": {
        "optional": {},
        "required": {
          "status": "String",
          "task": "String"
        }
      }
    }

.. [#] Using <http://www.teleport-json.org/>

----

Roadmap
-------

Automated backwards compatibility checking. (Could look something like this.)

.. code:: python

    from val import bc

    schema_v1 = Schema({'task': str})
    incompatible_v2 = Schema({
        'task': str,
        'status': str})
    bc.check(incompatible_v2, schema_v1)  # would return False

    combatible_v2 = Schema({
        'task': str,
        Optional('status'): str})
    bc.check(combatible_v2, schema_v1)  # would return True
