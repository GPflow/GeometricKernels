import gpflow
import meshzoo
import numpy as np
import polyscope as ps
import tensorflow as tf

from geometric_kernels.frontends import GPflowGeometricKernel
from geometric_kernels.kernels import MaternKarhunenLoeveKernel
from geometric_kernels.spaces import Mesh


class DefaultFloatZero(gpflow.mean_functions.Constant):
    """
    Simple zero mean function that uses gpflow's default_float
    as dtype instead of the default input's dtype. In our case this
    leads to dtype mismatch because the inputs are integer indices.
    """

    def __init__(self, output_dim=1):
        super().__init__()
        self.output_dim = output_dim
        del self.c

    def __call__(self, inputs):
        output_shape = tf.concat([tf.shape(inputs)[:-1], [self.output_dim]], axis=0)
        return tf.zeros(output_shape, dtype=gpflow.default_float())


# filename = Path(__file__).parent / "../teddy.obj"
# mesh = Mesh.load_mesh(str(filename))
# return mesh

resolution = 10
vertices, faces = meshzoo.icosa_sphere(resolution)
mesh = Mesh(vertices, faces)

nu = 1 / 2.0
truncation_level = 20
base_kernel = MaternKarhunenLoeveKernel(mesh, nu, truncation_level)
kernel = GPflowGeometricKernel(base_kernel)
num_data = 25


def get_data():
    _X = np.random.randint(mesh.num_vertices, size=(num_data, 1))
    _K = kernel.K(_X).numpy()
    _y = np.linalg.cholesky(_K + np.eye(num_data) * 1e-6) @ np.random.randn(num_data, 1)
    return _X, _y


X, y = get_data()

model = gpflow.models.GPR((X, y), kernel, mean_function=DefaultFloatZero(), noise_variance=1.1e-6)

X_test = np.arange(mesh.num_vertices).reshape(-1, 1)
m, v = model.predict_f(X_test)
m, v = m.numpy(), v.numpy()
sample = model.predict_f_samples(X_test).numpy()

ps.init()
ps_cloud = ps.register_point_cloud("my points", vertices[X.flatten()])
ps_cloud.add_scalar_quantity("data", y.flatten())


my_mesh = ps.register_surface_mesh("my mesh", vertices, faces, smooth_shade=True)
my_mesh.add_scalar_quantity(f"sample", sample.squeeze(), enabled=True)
my_mesh.add_scalar_quantity(f"mean", m.squeeze(), enabled=True)
my_mesh.add_scalar_quantity(f"variance", v.squeeze(), enabled=True)
ps.show()
