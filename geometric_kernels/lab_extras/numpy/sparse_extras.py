import lab as B
import scipy.sparse as sp
from lab import dispatch
from plum import Signature, Union

from .extras import _Numeric

"""
SparseArray defines a lab data type that covers all possible sparse
scipy arrays, so that multiple dispatch works with such arrays.
"""
SparseArray = Union[
    sp.bsr_matrix,
    sp.coo_matrix,
    sp.csc_matrix,
    sp.csr_matrix,
    sp.dia_matrix,
    sp.dok_matrix,
    sp.lil_matrix,
]


@dispatch
def degree(a: SparseArray):  # type: ignore
    """
    Given an adjacency matrix `a`, return a diagonal matrix
    with the col-sums of `a` as main diagonal - this is the
    degree matrix representing the number of nodes each node
    is connected to.
    """
    d = a.sum(axis=0)  # type: ignore
    return sp.spdiags(d, 0, d.size, d.size)


@dispatch
def eigenpairs(L: Union[SparseArray, _Numeric], k: int):
    """
    Obtain the k highest eigenpairs of a symmetric PSD matrix L.
    """
    if sp.issparse(L) and (k == L.shape[0]):
        L = L.toarray()
    return sp.linalg.eigsh(L, k, sigma=1e-8)


@dispatch
def set_value(a: Union[SparseArray, _Numeric], index: int, value: float):
    """
    Set a[index] = value.
    This operation is not done in place and a new array is returned.
    """
    a = a.copy()
    a[index] = value
    return a


""" Register methods for simple ops for a sparse array. """


def pinv(a: Union[SparseArray]):
    i, j = a.nonzero()
    if not (i == j).all():
        raise NotImplementedError(
            "pinv is not supported for non-diagonal sparse arrays."
        )
    else:
        a = sp.csr_matrix(a.copy())
        a[i, i] = 1 / a[i, i]
        return a


_SparseArray = Signature(SparseArray)

B.T.register(_SparseArray, lambda a: a.T)
B.shape.register(_SparseArray, lambda a: a.shape)
B.sqrt.register(_SparseArray, lambda a: a.sqrt())
B.any.register(_SparseArray, lambda a: bool((a == True).sum()))  # noqa

B.linear_algebra.pinv.register(_SparseArray, pinv)
