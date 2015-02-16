0.7:

  - Optional() no longer takes `default` and `null_values` arguments. These can
    and should be set on the value rather than the key. This was deprecated in
    0.5. Change your code as follows:
  
        ```python
        # before
        schema = Schema(
            {Optional('name', default='joe', null_values=('',)): str})

        # after
        schema = Schema(
            {Optional('name'): Schema(str, default='joe', null_values=('',))})
        ```

  - Falsy values such as `0`, `''`, `[]`, `{}`, False etc. are no longer
    considered "null values" w.r.t. whether or not to substitute them with
    a default value. If you do want these to be affected, pass them in
    `null_values`. (The only value considered to be a null value by default is
    None.)
