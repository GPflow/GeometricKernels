"""
Convenience utilities.
"""
import inspect
from typing import List, Type

import einops
import lab as B
from plum import Union

from geometric_kernels.lab_extras import get_random_state, restore_random_state


class OptionalMeta(type):
    def __getitem__(cls, args: Type):
        return Union[(None,) + (args,)]


class Optional(metaclass=OptionalMeta):
    pass


def chain(elements: B.Numeric, repetitions: List[int]) -> B.Numeric:
    """
    Repeats each element in `elements` by a certain number of repetitions as
    specified in `repetitions`.  The length of `elements` and `repetitions`
    should match.

    .. code:
        elements = ['a', 'b', 'c']
        repetitions = [2, 1, 3]
        out = chain(elements, repetitions)
        print(out)  # ['a', 'a', 'b', 'c', 'c', 'c']
    """
    values = [
        einops.repeat(elements[i : i + 1], "j -> (tile j)", tile=repetitions[i])
        for i in range(len(repetitions))
    ]
    return B.concat(*values, axis=0)


def make_deterministic(f, key):
    """
    Returns a deterministic version of a function that uses a random number generator.

    :param f: the function to make deterministic.
    :param key: the key used to generate the random state.

    :return: a function representing the deterministic version of the input function.

        .. Note:
            This function assumes that the input function has a 'key' argument
            or keyword-only argument that is used to generate random numbers.
            Otherwise, the function is returned as is.
    """
    f_argspec = inspect.getfullargspec(f)
    f_varnames = f_argspec.args
    key_argtype = None
    if "key" in f_varnames:
        key_argtype = "pos"
        key_position = f_varnames.index("key")
    elif "key" in f_argspec.kwonlyargs:
        key_argtype = "kwonly"

    if key_argtype is None:
        return f  # already deterministic

    saved_random_state = get_random_state(key)

    def deterministic_f(*args, **kwargs):
        restored_key = restore_random_state(key, saved_random_state)
        if key_argtype == "kwonly":
            kwargs["key"] = restored_key
            new_args = args
        elif key_argtype == "pos":
            new_args = args[:key_position] + (restored_key,) + args[key_position:]
        else:
            raise ValueError("Unknown key_argtype %s" % key_argtype)
        return f(*new_args, **kwargs)

    return deterministic_f


def ordered_pairwise_differences(X):
    """
    Compute the ordered pairwise differences between elements of a vector.

    :param X: a tensor of shape [B, D], where B is the batch size and D is the dimension.

    :return: a vector of shape [B, C], where C = D*(D-1)//2, with the ordered pairwise differences
            between elements of X. That is, the vector containing differences X[...,i]-X[...,j] where i < j.
    """
    diffX = B.expand_dims(X, -2) - B.expand_dims(X, -1)  # [B, D, D]
    # diffX[i, j] = X[j] - X[i]
    # lower triangle is i > j
    # so, lower triangle is X[k] - X[l] with k < l

    diffX = B.tril_to_vec(diffX, offset=-1)  # don't take the diagonal

    return diffX
