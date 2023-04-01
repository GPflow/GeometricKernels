"""
Feature maps
"""
from typing import Dict

import lab as B

from geometric_kernels.kernels import MaternKarhunenLoeveKernel
from geometric_kernels.lab_extras import from_numpy
from geometric_kernels.sampling.probability_densities import base_density_sample
from geometric_kernels.spaces import DiscreteSpectrumSpace, NoncompactSymmetricSpace


def deterministic_feature_map_compact(
    space: DiscreteSpectrumSpace,
    kernel: MaternKarhunenLoeveKernel,
):
    r"""
    Deterministic feature map for compact spaces based on the Laplacian eigendecomposition.

    :return: Callable
        Signature: (X, params, state, **kwargs)
        :param X: [N, D] points in the space to evaluate the map on.
        :param params: parameters of the kernel (lengthscale and smoothness).
        :param state: state of the kernel.
        :param **kwargs: unused.

        :return: `Tuple(features, context)` where `features` is [N, O] features,
                 and `context` is empty (no context).
    """

    def _map(X: B.Numeric, params, state, **kwargs) -> B.Numeric:
        """
        Feature map of the Matern kernel defined on DiscreteSpectrumSpace.

        :param X: points in the space to evaluate the map on.
        :param params: parameters of the kernel (lengthscale and smoothness).
        :param state: state of the kernel.
        :param **kwargs: unused.

        :return: `Tuple(features, context)` where `features` is [N, O] features,
                 and `context` is empty (no context).
        """
        assert "eigenvalues_laplacian" in state
        assert "eigenfunctions" in state

        repeated_eigenvalues = space.get_repeated_eigenvalues(kernel.num_eigenfunctions)
        spectrum = kernel._spectrum(
            repeated_eigenvalues**0.5,
            nu=params["nu"],
            lengthscale=params["lengthscale"],
        )

        weights = B.transpose(B.power(spectrum, 0.5))  # [1, M]
        Phi = state["eigenfunctions"]

        eigenfunctions = Phi.__call__(X, **params)  # [N, M]

        _context: Dict[str, str] = {}  # no context
        features = B.cast(B.dtype(X), eigenfunctions) * B.cast(
            B.dtype(X), weights
        )  # [N, M]
        return features, _context

    return _map


def random_phase_feature_map_compact(
    space: DiscreteSpectrumSpace,
    kernel: MaternKarhunenLoeveKernel,
    num_random_phases=3000,
):
    r"""
    Random phase feature map for compact spaces based on the Laplacian eigendecomposition.

    :param space: Space.
    :param kernel: kernel.

    :return: Callable
        Signature: (X, params, state, key, **kwargs)
        :param X: [N, D] points in the space to evaluate the map on.
        :param params: parameters of the kernel (lengthscale and smoothness).
        :param state: state of the kernel.
        :param key: random state, either `np.random.RandomState`, `tf.random.Generator`,
                    `torch.Generator` or `jax.tensor` (representing random state).

                     Note that for any backend other than `jax`, passing the same `key`
                     twice does not garantee that the feature map will be the same each time.
                     This is because these backends' random state has... a state.
                     One either has to recreate/restore the state each time or
                     make use of `geometric_kernels.utils.make_deterministic`.
        :param **kwargs: unused.

        :return: `Tuple(features, context)` where `features` is [N, O] features,
                 and `context` is `{'key': <new key>}`. `<new key>` is the new key
                 for jax, and the same random state (generator) for all other backends.
    """

    def _map(X: B.Numeric, params, state, key, **kwargs) -> B.Numeric:
        """
        :param X: [N, D] points in the space to evaluate the map on.
        :param params: parameters of the kernel (lengthscale and smoothness).
        :param state: state of the kernel.
        :param key: random state, either `np.random.RandomState`, `tf.random.Generator`,
                    `torch.Generator` or `jax.tensor` (representing random state).

                     Note that for any backend other than `jax`, passing the same `key`
                     twice does not garantee that the feature map will be the same each time.
                     This is because these backends' random state has... a state.
                     One either has to recreate/restore the state each time or
                     make use of `geometric_kernels.utils.make_deterministic`.
        :param **kwargs: unused.

        :return: `Tuple(features, context)` where `features` is [N, O] features,
                 and `context` is `{'key': <new key>}`. `<new key>` is the new key
                 for jax, and the same random state (generator) for all other backends.
        """
        key, random_phases = space.random(key, num_random_phases)  # [O, D]
        eigenvalues = state["eigenvalues_laplacian"]

        spectrum = kernel._spectrum(
            eigenvalues**0.5,
            nu=params["nu"],
            lengthscale=params["lengthscale"],
        )

        weights = B.power(spectrum, 0.5)  # [L, 1]
        Phi = state["eigenfunctions"]

        # X [N, D]
        random_phases_b = B.cast(B.dtype(X), from_numpy(X, random_phases))
        embedding = B.cast(
            B.dtype(X), Phi.phi_product(X, random_phases_b, **params)
        )  # [N, O, L]
        weights_t = B.cast(B.dtype(X), B.transpose(weights))

        features = B.reshape(embedding * weights_t, B.shape(X)[0], -1)  # [N, O*L]
        _context: Dict[str, str] = {"key": key}
        return features, _context

    return _map


def random_phase_feature_map_noncompact(
    space: NoncompactSymmetricSpace, num_random_phases=3000
):
    r"""
    Random phase feature map for noncompact symmetric space based on naive algorithm.

    :param space: Space.
    :param num_random_phases: number of random phases to use.

    :return: Callable
            Signature: (X, params, state, key, **kwargs)
            :param X: [N, D] points in the space to evaluate the map on.
            :param params: parameters of the feature map (lengthscale and smoothness).
            :param state: unused.
            :param key: random state, either `np.random.RandomState`, `tf.random.Generator`,
                        `torch.Generator` or `jax.tensor` (representing random state).

                         Note that for any backend other than `jax`, passing the same `key`
                         twice does not garantee that the feature map will be the same each time.
                         This is because these backends' random state has... a state.
                         One either has to recreate/restore the state each time or
                         make use of `geometric_kernels.utils.make_deterministic`.
            :param **kwargs: unused.

            :return: `Tuple(features, context)` where `features` is [N, O] features,
                     and `context` is `{'key': <new key>}`. `<new key>` is the new key
                     for jax, and the same random state (generator) for all other backends.
    """

    def _map(X: B.Numeric, params, state, key, **kwargs) -> B.Numeric:
        """
        :param X: [N, D] points in the space to evaluate the map on.
        :param params: parameters of the feature map (lengthscale and smoothness).
        :param state: unused.
        :param key: random state, either `np.random.RandomState`, `tf.random.Generator`,
                    `torch.Generator` or `jax.tensor` (representing random state).

                     Note that for any backend other than `jax`, passing the same `key`
                     twice does not garantee that the feature map will be the same each time.
                     This is because these backends' random state has... a state.
                     One either has to recreate/restore the state each time or
                     make use of `geometric_kernels.utils.make_deterministic`.
        :param **kwargs: unused.

        :return: `Tuple(features, context)` where `features` is [N, O] features,
                 and `context` is `{'key': <new key>}`. `<new key>` is the new key
                 for jax, and the same random state (generator) for all other backends.
        """
        key, random_phases = space.random_phases(key, num_random_phases)  # [O, D]

        key, random_lambda = base_density_sample(
            key, (num_random_phases,), params, space.dimension
        )  # [O, ]

        # X [N, D]
        random_phases_b = B.expand_dims(
            B.cast(B.dtype(X), from_numpy(X, random_phases))
        )  # [1, O, D]
        random_lambda_b = B.expand_dims(
            B.cast(B.dtype(X), from_numpy(X, random_lambda))
        )  # [1, O]

        p = space.power_function(random_lambda_b, X[:, None], random_phases_b)  # [N, O]
        c = space.inv_harish_chandra(random_lambda_b)  # [1, O]

        out = B.concat(B.real(p) * c, B.imag(p) * c, axis=-1)  # [N, 2*O]
        normalizer = B.sqrt(B.sum(out**2, axis=-1, squeeze=False))
        out = out / normalizer

        _context: Dict[str, B.types.RandomState] = {"key": key}
        return out, _context

    return _map