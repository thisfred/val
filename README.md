lazyval
=======

(Mostly) Functional schema validator

Inspired by the wonderful ideas in schema and flatland: 

https://github.com/halst/schema
http://discorporate.us/projects/flatland/

many of which I outright stole.

The goal is to make validation faster, while keeping the very pythonic and minimal schema style, at the expense of more advanced features in schema.

Current status is: use at your peril, everything subject to change.

I have not optimized much, but for the kind of schemas I need (specifically: to validate JSON that has been loaded into python structures,) I have extremely anecdotal evidence that it's around 10x faster than both schema and flatland. (Again, that is mostly because it does way less, and I intend to keep it that way.)

The schemas understood by lazyval are very similar to the ones in schema, but without the need for a class:

    lazy_schema = {
        'invisible': bool,
        'immutable': bool,
        Optional('favorite_colors'): [str],
        Optional('favorite_foods'): [str],
        Optional('lucky_number'): Or(int, None),
        Optional('shoe_size'): int,
        Optional('mother'): {
            'name': str,
            'nested': {'id': str}},
        Optional('father'): {
            'name': str,
            'nested': {'id': str}}}
