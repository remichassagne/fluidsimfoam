from math import cos, pi
from textwrap import dedent

from inflection import underscore

from fluidsimfoam.foam_input_files import (
    BlockMeshDict,
    ConstantFileHelper,
    FoamInputFile,
    FvSchemesHelper,
    VolScalarField,
    VolVectorField,
)

from fluidsimfoam.foam_input_files.blockmesh import (
    Point,
    SimpleGrading,
    Vertex,
)
from fluidsimfoam.output import Output


def add_default_boundaries(field):
    for name, type_ in (
        ("inlet", "cyclic"),
        ("outlet", "cyclic"),
        ("top", "zeroGradient"),
        ("bottom", "zeroGradient"),
        ("frontAndBackPlanes", "empty"),
    ):
        field.set_boundary(name, type_)


def make_scalar_field(name, dimension, values=None):
    field = VolScalarField(name, dimension, values=values)
    add_default_boundaries(field)
    return field


def make_vector_field(name, dimension, values=None):
    field = VolVectorField(name, dimension, values=values)
    add_default_boundaries(field)
    return field


code_fv_options = dedent(
    r"""
atmCoriolisUSource1
{
    type            atmCoriolisUSource;
    atmCoriolisUSourceCoeffs
    {
        selectionMode   all;
        Omega           (0 7.2921e-5 0);
    }
}
"""
)


class OutputPHill(Output):
    """Output for the phill solver"""

    variable_names = ["U", "rhok", "p_rgh", "T", "alphat"]
    system_files_names = Output.system_files_names + ["blockMeshDict"]
    constant_files_names = [
        "g",
        "fvOptions",
        "MRFProperties",
        "transportProperties",
        "turbulenceProperties",
    ]

    default_control_dict_params = Output.default_control_dict_params.copy()
    default_control_dict_params.update(
        {
            "application": "buoyantBoussinesqPimpleFoam",
            "startFrom": "latestTime",
            "endTime": 1200000,
            "deltaT": 10,
            "writeControl": "adjustableRunTime",
            "writeInterval": 5000,
            "adjustTimeStep": "on",
            "maxCo": 0.6,
            "maxAlphaCo": 0.6,
            "maxDeltaT": 1,
        }
    )

    helper_fv_schemes = FvSchemesHelper(
        ddt="default         Euler implicit",
        grad="default         Gauss linear",
        div="""
        default         none
        div(phi,U)      Gauss upwind
        div(phi,T)      Gauss upwind
        div(phi,rhok)      Gauss upwind
        div(phi,R)      Gauss upwind
        div(R)          Gauss linear
        div((nuEff*dev2(T(grad(U))))) Gauss linear
        div((nuEff*dev(T(grad(U))))) Gauss linear
""",
        laplacian="""
        default         Gauss linear corrected
""",
        interpolation={
            "default": "linear",
        },
        sn_grad={
            "default": "uncorrected",
        },
    )

    helper_transport_properties = ConstantFileHelper(
        "transportProperties",
        {
            "transportModel": "Newtonian",
            "nu": 1.0e-2,
            "Pr": 10,
            "beta": 2.23e-4,
            "TRef": 1.0e-2,
            "Prt": 1e2,
        },
        dimensions={
            "nu": "m^2/s",
            "Pr": "1",
            "beta": "1/K",
            "TRef": "K",
            "Prt": "1",
        },
        default_dimension="",
        comments={},
    )

    @classmethod
    def _complete_params_block_mesh_dict(cls, params):
        super()._complete_params_block_mesh_dict(params)
        default = {"nx": 20, "ny": 50, "nz": 1}
        default.update({"lx": 2000, "ly": 5000, "lz": 0.01, "scale": 1})
        for key, value in default.items():
            params.block_mesh_dict[key] = value

    def make_code_block_mesh_dict(self, params):
        nx = params.block_mesh_dict.nx
        ny = params.block_mesh_dict.ny
        nz = params.block_mesh_dict.nz

        lx = params.block_mesh_dict.lx
        ly = params.block_mesh_dict.ly
        lz = params.block_mesh_dict.lz

        bmd = BlockMeshDict()
        bmd.set_scale(params.block_mesh_dict.scale)

        h_max = 80
        basevs = [
            Vertex(0, h_max, lz, "v0"),
            Vertex(lx, h_max, lz, "v1"),
            Vertex(lx, ly, lz, "v2"),
            Vertex(0, ly, lz, "v3"),
        ]

        for v in basevs:
            bmd.add_vertex(v.x, v.y, 0, v.name + "-0")
        for v in basevs:
            bmd.add_vertex(v.x, v.y, v.z, v.name + "+z")

        b0 = bmd.add_hexblock(
            ("v0-0", "v1-0", "v2-0", "v3-0", "v0+z", "v1+z", "v2+z", "v3+z"),
            (nx + 1, ny, nz),
            "b0",
            SimpleGrading(1, [[0.1, 0.25, 41.9], [0.9, 0.75, 1]], 1),
        )

        x_dot = []
        y_dot = []
        dots = []
        h_max = 80
        for dot in range(nx + 1):
            x_dot.append(dot * lx / nx)
            y_dot.append(
                (h_max / 2)
                * (1 - cos(2 * pi * min(abs((x_dot[dot] - (lx / 2)) / lx), 1)))
            )
            dots.append([x_dot[dot], y_dot[dot]])

        bmd.add_splineedge(
            ["v0-0", "v1-0"],
            "spline0",
            [Point(dot[0], dot[1], 0) for dot in dots],
        )
        bmd.add_splineedge(
            ["v0+z", "v1+z"],
            "spline1",
            [Point(dot[0], dot[1], lz) for dot in dots],
        )

        bmd.add_boundary("wall", "top", [b0.face("n")])
        bmd.add_boundary("wall", "bottom", [b0.face("s")])
        bmd.add_cyclic_boundaries("outlet", "inlet", b0.face("e"), b0.face("w"))
        bmd.add_boundary(
            "empty",
            "frontandbackplanes",
            [
                b0.face("b"),
                b0.face("t"),
            ],
        )

        return bmd.format(sort_vortices="as_added")

    def make_tree_alphat(self, params):
        return make_scalar_field("alphat", dimension="m^2/s", values=0)

    def make_tree_p_rgh(self, params):
        return make_scalar_field("p_rgh", dimension="m^2/s^2", values=0)

    def make_tree_rhok(self, params):
        return make_scalar_field("rhok", dimension="", values=1.15)

    def make_tree_t(self, params):
        return make_scalar_field("T", dimension="K", values=300)

    def make_tree_u(self, params):
        field = make_vector_field("U", dimension="m/s", values=[0.1, 0, 0])
        field.set_boundary("top", "slip")
        field.set_boundary("bottom", "noSlip")
        return field
