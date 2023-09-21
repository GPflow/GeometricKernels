"""
A wrapper around different kernels and feature maps that dispatches on space.
"""
from plum import dispatch

from geometric_kernels.kernels.feature_maps import (
    deterministic_feature_map_compact,
    random_phase_feature_map_noncompact,
    rejection_sampling_feature_map_hyperbolic,
    rejection_sampling_feature_map_spd,
)
from geometric_kernels.kernels.geometric_kernels import (
    MaternFeatureMapKernel,
    MaternKarhunenLoeveKernel,
)
from geometric_kernels.spaces import (
    DiscreteSpectrumSpace,
    Graph,
    Hyperbolic,
    Mesh,
    NoncompactSymmetricSpace,
    Space,
    SymmetricPositiveDefiniteMatrices,
)


@dispatch
def default_feature_map(space: DiscreteSpectrumSpace, *, num, kernel):
    return deterministic_feature_map_compact(space, kernel)


@dispatch
def default_feature_map(space: NoncompactSymmetricSpace, *, num, kernel):
    return random_phase_feature_map_noncompact(space, num)


@dispatch
def default_feature_map(space: Hyperbolic, *, num, kernel):
    return rejection_sampling_feature_map_hyperbolic(space, num)


@dispatch
def default_feature_map(space: Hyperbolic, *, num, kernel):
    return rejection_sampling_feature_map_hyperbolic(space, num)


@dispatch
def default_feature_map(space: SymmetricPositiveDefiniteMatrices, *, num, kernel):
    """
    Note parameter `kernel` is not used, just pass None.
    """
    return rejection_sampling_feature_map_spd(space, num)


@dispatch
def default_num(space: Mesh):
    return min(MaternGeometricKernel._DEFAULT_NUM_EIGENFUNCTIONS, space.num_vertices)


@dispatch
def default_num(space: Graph):
    return min(MaternGeometricKernel._DEFAULT_NUM_EIGENFUNCTIONS, space.num_vertices)


@dispatch
def default_num(space: DiscreteSpectrumSpace):
    return MaternGeometricKernel._DEFAULT_NUM_LEVELS


@dispatch
def default_num(space: NoncompactSymmetricSpace):
    return MaternGeometricKernel._DEFAULT_NUM_RANDOM_PHASES


class MaternGeometricKernel:
    """
    This class represents a Matérn geometric kernel that "just works".

    Upon creation, this class unpacks into a specific geometric kernel based
    on the provided Space, and the associated feature map.
    """

    _DEFAULT_NUM_EIGENFUNCTIONS = 1000
    _DEFAULT_NUM_LEVELS = 35
    _DEFAULT_NUM_RANDOM_PHASES = 3000

    def __new__(
        cls,
        space: Space,
        num=None,
        normalize=True,
        return_feature_map=False,
        **kwargs,
    ):
        r"""
        Construct a kernel and (if `return_feature_map` is `True`) a
        feature map on `space`.

        :param space: space to construct the kernel on.
        :param num: if provided, controls the "order of approximation"
            of the kernel. For the discrete spectrum spaces, this means
            the number of "levels" that go into the truncated series that
            defines the kernel (for example, these are unique eigenvalues
            for the `Hypersphere` or eigenvalues with repetitions for
            the `Graph` or for the `Mesh`). For the noncompact symmetric
            spaces, this is the number of random phases to construct the
            kernel.
        :param normalize: normalize kernel variance. The exact normalization
            technique varies from space to space.
        :param return_feature_map: if `True`, return a feature map (needed
            e.g. for efficient sampling from Gaussian processes) along with
            the kernel. Default is `False`.
        :param ``**kwargs``: any additional keyword arguments to be passed to
            the kernel (like `key`). **Important:** for non-compact symmetric
            spaces (Hyperbolic, SPD) the `key` **must** be provided in kwargs.
        """

        if isinstance(space, DiscreteSpectrumSpace):
            num = num or default_num(space)
            kernel = MaternKarhunenLoeveKernel(space, num, normalize=normalize)
            feature_map = default_feature_map(space, kernel=kernel, num=num)

        elif isinstance(space, NoncompactSymmetricSpace):
            num = num or default_num(space)
            if "key" in kwargs:
                key = kwargs["key"]
            else:
                raise ValueError(
                    (
                        "MaternGeometricKernel for %s requires mandatory"
                        " keyword argument 'key' which is a random number"
                        " generator specific to the backend used"
                    )
                    % str(type(space))
                )
            feature_map = default_feature_map(space, kernel=None, num=num)
            kernel = MaternFeatureMapKernel(
                space, feature_map, key, normalize=normalize
            )
        else:
            raise NotImplementedError

        if return_feature_map:
            return kernel, feature_map
        else:
            return kernel
