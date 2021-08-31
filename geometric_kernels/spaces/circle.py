"""
Spaces for which there exist analytical expressions for the manifold
and the eigenvalues and functions. Examples include the `Circle` and the `Hypersphere`.
The Geomstats package is used for most of the geometric calculations.
"""
from typing import Callable, Optional

import geomstats as gs
import numpy as np
import tensorflow as tf

from geometric_kernels.eigenfunctions import EigenfunctionWithAdditionTheorem, Eigenfunctions
from geometric_kernels.spaces import SpaceWithEigenDecomposition
from geometric_kernels.types import TensorLike


def cartesian_to_polar(X: TensorLike) -> TensorLike:
    """
    :param X: Cartesian coordinates on the circle, [N, 2].
        This means their norm equals one.
    :return: angle [N, 1]
    """
    return tf.reshape(tf.math.atan2(X[:, 1], X[:, 0]), (-1, 1))


class SinCosEigenfunctions(EigenfunctionWithAdditionTheorem):
    """
    Eigenfunctions Laplace-Beltrami operator on the circle correspond
    to the Fourier basis, i.e. sin and cosines..
    """

    def __init__(self, num_eigenfunctions: int) -> int:
        assert (
            num_eigenfunctions % 2 == 1
        ), "num_eigenfunctions needs to be odd to include all eigenfunctions within a level."
        assert num_eigenfunctions >= 1

        self._num_eigenfunctions = num_eigenfunctions
        # We know `num_eigenfunctions` is odd, therefore:
        self._num_levels = num_eigenfunctions // 2 + 1

    def __call__(self, X: TensorLike) -> TensorLike:
        """
        :param X: cartesian coordinates on the circle, [N, 2].
        """
        const = 2.0 ** 0.5
        theta = cartesian_to_polar(X)
        values = []
        for level in range(self.num_levels):
            if level == 0:
                values.append(tf.ones_like(theta))
            else:
                freq = 1.0 * level
                values.append(const * tf.math.cos(freq * theta))
                values.append(const * tf.math.sin(freq * theta))

        return tf.concat(values, axis=1)  # [N, M]

    def _addition_theorem(self, X: TensorLike, X2: TensorLike) -> TensorLike:
        r"""
        Returns the result of applying the additional theorem when
        summing over all the eigenfunctions within a level, for each level

        Concretely in the case for inputs on the sphere S^1:

        .. math:
            \sin(l \theta_1) \sin(l \theta_2) + \cos(l \theta_1) \cos(l \theta_2)
                = N_l \cos(l (\theta_1 - \theta_2)),
        where N_l = 1 for l = 0, else N_l = 2.

        :param X: difference between angles
            theta_1 and theta_2 of 2 inputs, [N, 1]
        :return: [N, L], L = num_levels

        :param X: [N, 2]
        :param X2: [N2, 2]
        :return: Evaluate the sum of eigenfunctions on each level. Returns
            a value for each level [N, N2, L]
        """
        theta = cartesian_to_polar(X)  # [N, 1]
        theta2 = cartesian_to_polar(X2)  # [N2, 1]
        diff_theta = theta[:, None, :] - theta2[None, :, :]  # [N, N2, 1]
        freqs = tf.range(self.num_levels, dtype=X.dtype)  # [L]
        values = tf.math.cos(freqs[None, None, :] * diff_theta)  # [N, N2, L]
        values = self.num_eigenfunctions_per_level[None, None, :] * values
        return values  # [N, N2, L]

    def _addition_theorem_diag(self, X: TensorLike) -> TensorLike:
        """
        Returns the sum of eigenfunctions on a level for which we have a simplified expression

        :param X: [N, 1]
        :return: Evaluate the sum of eigenfunctions on each level. Returns
            a value for each level [N, L]
        """
        N = tf.shape(X)[0]
        ones = tf.ones((N, self.num_levels), dtype=X.dtype)  # [N, L]
        value = ones * self.num_eigenfunctions_per_level[None, :]
        return value  # [N, L]

    @property
    def num_eigenfunctions(self) -> int:
        """Number of eigenfunctions, M"""
        return self._num_eigenfunctions

    @property
    def num_levels(self) -> int:
        """
        Number of levels, L

        For each level except the first where there is just one, there are two
        eigenfunctions.
        """
        return self._num_levels

    @property
    def num_eigenfunctions_per_level(self) -> np.ndarray:
        """Number of eigenfunctions per level, [N_l]_{l=0}^{L-1}"""
        return np.array(
            [1 if level == 0 else 2 for level in range(self.num_levels)]
        )


class Circle(SpaceWithEigenDecomposition, gs.geometry.hypersphere.Hypersphere):
    r"""
    Circle :math:`\mathbb{S}^1` manifold with sinusoids and cosines eigenfunctions.
    """

    def __init__(self):
        super().__init__(dim=1)

    def is_tangent(
        self,
        vector: TensorLike,
        base_point: Optional[TensorLike] = None,
        atol: float = gs.geometry.manifold.ATOL,
    ) -> bool:
        """
        Check whether the `vector` is tangent at `base_point`.
        :param vector: shape=[..., dim]
            Vector to evaluate.
        :param base_point: shape=[..., dim]
            Point on the manifold. Defaults to `None`.
        :param atol: float
            Absolute tolerance.
            Optional, default: 1e-6.
        :return: Boolean denoting if vector is a tangent vector at the base point.
        """
        raise NotImplementedError("`is_tangent` is not implemented for `Hypersphere`")

    @property
    def dimension(self) -> int:
        return 2

    def get_eigenfunctions(self, num: int) -> Eigenfunctions:
        """
        :param num: number of eigenfunctions returned.
        """
        return SinCosEigenfunctions(num)

    def get_eigenvalues(self, num: int) -> TensorLike:
        """
        First `num` eigenvalues of the Laplace-Beltrami operator

        :return: [num, 1] array containing the eigenvalues
        """
        return tf.range(num, dtype='float64') ** 2.0
