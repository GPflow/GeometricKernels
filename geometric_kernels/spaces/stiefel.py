import lab as B
import numpy as np
from opt_einsum import contract as einsum

from geometric_kernels.lab_extras import qr
from geometric_kernels.spaces.homogeneous_spaces import (
    CompactHomogeneousSpace,
    CompactHomogeneousSpaceAddtitionTheorem,
)
from geometric_kernels.spaces.so import SOGroup


def hook_content_formula(lmd, n):
    numer = 1
    denom = 1

    l_cols = [sum([row_l >= i + 1 for row_l in lmd]) for i in range(lmd[0])]
    for id_row, l_row in enumerate(lmd):
        for id_col in range(l_row):
            numer *= n + id_col - id_row
            denom *= l_cols[id_col] + l_row - id_row - id_col - 1

    return numer / denom


class StiefelEigenfunctions(CompactHomogeneousSpaceAddtitionTheorem):
    def _compute_projected_character_value_at_e(self, signature):
        """
        Value of character on class of identity element is equal to the dimension of invariant space
        In case of Stiefel manifold it could be computed using hook content formula
        :param signature:
        :return: int
        """
        m_ = min(self.M.m, self.M.n - self.M.m)
        if m_ < self.M.G.rank and signature[m_] > 0:
            return 0
        signature_abs = tuple(abs(x) for x in signature)
        return hook_content_formula(signature_abs, m_)


class Stiefel(CompactHomogeneousSpace):
    r"""
    Stifiel manifold V(n, m) = SO(n) / SO(n-m).
    """

    def __new__(cls, n, m, key, average_order=1000):
        assert n > m, "n should be greater than m"
        H = SOGroup(n - m)
        G = SOGroup(n)
        key, H_samples = H.random(key, average_order)
        new_space = super().__new__(cls)
        new_space.__init__(G=G, H=H, H_samples=H_samples, average_order=average_order)
        new_space.n = n
        new_space.m = m
        new_space.dim = G.dim - H.dim
        return key, new_space

    def project_to_manifold(self, g):
        return g[..., : self.m]

    def embed_manifold(self, x):
        g, r = qr(x)
        r_diag = einsum("...ii->...i", r[..., : self.m, : self.m])
        r_diag = B.concat(
            r_diag, B.ones(B.dtype(x), *x.shape[:-2], self.n - self.m), axis=-1
        )
        g = g * r_diag[:, None]
        diff = 2 * (B.all(B.abs(g[..., : self.m] - x) < 1e-5, axis=-1) - 0.5)
        g = g * diff[..., None]
        det_sign_g = B.sign(B.det(g))
        g[:, :, -1] *= det_sign_g[:, None]

        assert B.all((B.abs(x - g[:, :, : x.shape[-1]])) < 1e-6)
        return g

    def embed_stabilizer(self, h):
        zeros = B.zeros(B.dtype(h), *h.shape[:-2], self.m, self.n - self.m)
        zeros_t = B.transpose(zeros)
        eye = B.tile(
            B.eye(B.dtype(h), self.m, self.m).reshape(
                *([1] * (len(h.shape) - 2)), self.m, self.m
            ),
            *h.shape[:-2],
            1,
            1,
        )
        l, r = B.concat(eye, zeros_t, axis=-2), B.concat(zeros, h, axis=-2)
        res = B.concat(l, r, axis=-1)
        return res

    @property
    def dimension(self) -> int:
        return self.dim

    def get_eigenfunctions(self, num: int) -> CompactHomogeneousSpaceAddtitionTheorem:
        """
        :param num: number of eigenfunctions returned.
        """
        eigenfunctions = StiefelEigenfunctions(self, num, self.H_samples)
        return eigenfunctions

    def get_repeated_eigenvalues(self, num: int) -> B.Numeric:
        pass

    def get_eigenvalues(self, num: int) -> B.Numeric:
        """
        First `num` eigenvalues of the Laplace-Beltrami operator
        :return: [num, 1] array containing the eigenvalues
        """
        eigenfunctions = StiefelEigenfunctions(self, num, self.H_samples)
        eigenvalues = np.array(eigenfunctions._eigenvalues)
        return B.reshape(eigenvalues, -1, 1)  # [num, 1]

    def random(self, key, number):
        key, raw_samples = self.G.random(key, number)
        return key, self.project_to_manifold(raw_samples)