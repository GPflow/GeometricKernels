from typing import Any, List, Optional

import lab as B
import numpy as np
from lab import dispatch
from plum import Union

_Numeric = Union[B.Number, B.NPNumeric]


@dispatch
def take_along_axis(a: _Numeric, index: _Numeric, axis: int = 0) -> _Numeric:  # type: ignore
    """
    Gathers elements of `a` along `axis` at `index` locations.
    """
    return np.take_along_axis(a, index, axis=axis)


@dispatch
def from_numpy(_: B.NPNumeric, b: Union[List, B.NPNumeric, B.Number]):  # type: ignore
    """
    Converts the array `b` to a tensor of the same backend as `a`
    """
    return np.array(b)


@dispatch
def trapz(y: _Numeric, x: _Numeric, dx: _Numeric = 1.0, axis: int = -1):  # type: ignore
    """
    Integrate along the given axis using the composite trapezoidal rule.
    """
    return np.trapz(y, x, dx, axis)


@dispatch
def qr(a: _Numeric):
    """
    Compute QR factorization of a matrix.
    """
    return np.linalg.qr(a)


@dispatch
def norm(x: _Numeric, ord: Optional[Any] = None, axis: Optional[int] = None):  # type: ignore
    """
    Matrix or vector norm.
    """
    return np.linalg.norm(x, ord=ord, axis=axis)


@dispatch
def logspace(start: _Numeric, stop: _Numeric, num: int = 50, base: _Numeric = 50.0):  # type: ignore
    """
    Return numbers spaced evenly on a log scale.
    """
    return np.logspace(start, stop, num, base=base)


@dispatch
def degree(a: _Numeric):  # type: ignore
    """
    Given an adjacency matrix `a`, return a diagonal matrix
    with the col-sums of `a` as main diagonal - this is the
    degree matrix representing the number of nodes each node
    is connected to.
    """
    degrees = a.sum(axis=0)  # type: ignore
    return np.diag(degrees)


@dispatch
def dtype_double(reference: B.NPRandomState):  # type: ignore
    """
    Return `double` dtype of a backend based on the reference.
    """
    return np.float64


@dispatch
def dtype_integer(reference: B.NPRandomState):  # type: ignore
    """
    Return `int` dtype of a backend based on the reference.
    """
    return np.int64
