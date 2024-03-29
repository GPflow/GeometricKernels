from typing import List

import lab as B
from lab import dispatch
from lab.util import abstract
from plum import Union


@dispatch
@abstract()
def take_along_axis(a: B.Numeric, index: B.Numeric, axis: int = 0):
    """
    Gathers elements of `a` along `axis` at `index` locations.
    """


@dispatch
@abstract()
def from_numpy(_: B.Numeric, b: Union[List, B.Numeric, B.NPNumeric]):
    """
    Converts the array `b` to a tensor of the same backend as `a`
    """


@dispatch
@abstract()
def trapz(y: B.Numeric, x: B.Numeric, dx: B.Numeric = 1.0, axis: int = -1):
    """
    Integrate along the given axis using the trapezoidal rule.
    """


@dispatch
@abstract()
def logspace(start: B.Numeric, stop: B.Numeric, num: int = 50):
    """
    Return numbers spaced evenly on a log scale.
    """


def cosh(x: B.Numeric) -> B.Numeric:
    r"""
    Compute hyperbolic cosine using the formula

    .. math::
        \textrm{cosh}(x) = \frac{\exp(x) + \exp(-x)}{2}.
    """
    return 0.5 * (B.exp(x) + B.exp(-x))


def sinh(x: B.Numeric) -> B.Numeric:
    r"""
    Compute hyperbolic sine using the formula

    .. math::
        \textrm{sinh}(x) = \frac{\exp(x) - \exp(-x)}{2}.
    """
    return 0.5 * (B.exp(x) - B.exp(-x))


@dispatch
@abstract()
def degree(a):
    """
    Given an adjacency matrix `a`, return a diagonal matrix
    with the col-sums of `a` as main diagonal - this is the
    degree matrix representing the number of nodes each node
    is connected to.
    """


@dispatch
@abstract()
def eigenpairs(L, k: int):
    """
    Obtain the k highest eigenpairs of a symmetric PSD matrix L.
    """


@dispatch
@abstract()
def set_value(a, index: int, value: float):
    """
    Set a[index] = value.
    This operation is not done in place and a new array is returned.
    """
