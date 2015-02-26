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

Let's say we have a REST application for storing and managing todo items.

An example todo item might look like this:

.. code:: python

    {"task": "shave yak",
     "priority": 1}

----

Straw Man example: 

.. code:: python

    def post_todo(request):
        todo = request.json
        if 'task' not in todo:
            raise BadRequest("Missing field 'task'.")

        value = todo['task']
        if not isinstance(value, str):
            raise BadRequest("Value of field 'task' is of wrong type.")

        if 'priority' not in todo:
            raise BadRequest("Missing field 'priority'.")

        value = todo['priority']
        if not isinstance(value, int):
            raise BadRequest("Value of field 'priority' is of wrong type.")

        # Actually do something with `todo`.

And now do the same with small variations for PUT, DELETE, and any other
endpoints that accept (lists of) the same type. And then for all other types of
objects your application needs to be able to understand.

----

Same functionality using val:

.. code:: python

    TODO_SCHEMA = Schema({
        'task': str,
        'priority': int})

    def post_todo(request):
        try:
            todo = TODO_SCHEMA.validate(request.json)
        except NotValid as ex:
            raise BadRequest.from(ex)
        # Actually do something with `todo`.

- Declare schemas in a way that resembles valid input.
- Less logic, less repetition within handlers.
- Reusable and composable schemas.

----

Can be further refactored, for instance:

.. code:: python

    class HandlerBase(object):

        schema = None

        def get_validated_json(unvalidated):
            try:
                return self.schema.validate(unvalidated)
            except NotValid as ex:
                raise BadRequest.from(ex)

    class TodoHandler(HandlerBase):

        schema = TODO_SCHEMA

        def handle(request):
            todo = self.get_validated_json(request.json)
            # Actually do something with `todo`.

----


.. code:: python

    >>> from val import Schema

    >>> todo_schema = Schema({
    ...     'task': str,
    ...     'priority': int})

    >>> todo_schema.validate({'task': 'shave yak'})
    Traceback (most recent call last):
        ...
    val.NotValid: missing key: 'priority'

    >>> todo_schema.validate({'task': 'paint shed', 'priority': 'high'})
    Traceback (most recent call last):
        ...
    val.NotValid: 'priority': 'high' is not of type <class 'int'>

Sensible error messages, that can be forwarded to clients.

----

Schemas can be shared between python libraries / services, and published as
part of the documentation to aid client developers. For clients in other
languages, teleport\ [#]_ schemas can be published, and kept in sync with the
code through doctests:

.. code:: python

    >>> from val import tp

    >>> print(tp.document(todo_schema))
    {
      "Struct": {
        "optional": {},
        "required": {
          "priority": "Integer",
          "task": "String"
        }
      }
    }

.. [#] <http://www.teleport-json.org/>

----

Roadmap: Automated backwards compatibility checking. (Could look something like
this.  100% hand waving.)

.. code:: python

    from val import bc

    schema_v1 = Schema({'task': str, 'priority': int})
    incompatible_v2 = Schema({'task': str})
    bc.check(incompatible_v2, schema_v1)
    # ^ would return False, because `priority` is suddenly no longer valid.

    combatible_v2 = Schema({
        'task': str,
        Optional('priority'): int,
        Optional('status'): str})
    bc.check(combatible_v2, schema_v1)
    # ^ would return True, because changing a field from required to
    # optional is backwards compatible, as is adding new optional fields.
