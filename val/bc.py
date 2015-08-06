"""Backwards Compatility."""

from val._val import Validator, determine_keys


class BackwardsIncompatible(Exception):
    pass


def is_backward_compatible(new, old):
    if new.definition == old.definition:
        return True

    old_keys = determine_keys(old.definition)
    new_keys = determine_keys(new.definition)
    try:
        checked = check_old_required_keys(new_keys=new_keys, old_keys=old_keys)
    except BackwardsIncompatible:
        return False

    return check_new_required_keys(new_keys=new_keys, checked=checked)


def check_new_required_keys(new_keys, checked):
    for key in new_keys.required:
        if key in checked:
            continue

        return False

    return True


def check_old_required_keys(new_keys, old_keys):
    checked = set()
    for key in old_keys.required:
        if key in new_keys.required:
            if not is_compatible(new_keys.required[key],
                                 old_keys.required[key]):
                raise BackwardsIncompatible

            checked.add(key)
            continue

        if key in new_keys.optional:
            if not is_compatible(new_keys.optional[key],
                                 old_keys.required[key]):
                raise BackwardsIncompatible

            continue  # pragma: nocover

        raise BackwardsIncompatible

    return checked


def is_compatible(new, old):
    if new == old:
        return True

    if all(isinstance(x, Validator) for x in (new, old)):
        if new.is_more_general_than(old):
            return True

    return False
