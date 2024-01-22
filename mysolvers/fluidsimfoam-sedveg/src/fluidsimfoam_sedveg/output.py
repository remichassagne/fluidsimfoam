from fluidsimfoam.foam_input_files import (
    BlockMeshDict,
    ConstantFileHelper,
    FvSchemesHelper,
    VolScalarField,
    VolVectorField,
)

from fluidsimfoam.output import Output


class OutputSedveg(Output):
    name_variables = [
        "Theta",
        "U.a",
        "U.b",
        "U.c",
        "alpha.a",
        "alpha.c",
        "alphaPlastic",
        "delta",
        "epsilon.b",
        "k.b",
        "ks.b",
        "kw.b",
        "muI",
        "nut.b",
        "omega.b",
        "omegas.b",
        "omegaw.b",
        "p_rbgh",
        "pa",
    ]
    name_system_files = [
        "blockMeshDict",
        "controlDict",
        "fvSchemes",
        "fvSolution",
        "decomposeParDict"
    ]
    name_constant_files = [
        "filterProperties",
        "forceProperties",
        "g",
        "granularRheologyProperties",
        "interfacialProperties",
        "kineticTheoryProperties",
        "ppProperties",
        "transportProperties",
        "turbulenceProperties.a",
        "turbulenceProperties.b",
        "twophaseRASProperties",
    ]
    internal_symlinks = {}

    # _helper_control_dict = None
    # can be replaced by:
    _helper_control_dict = Output._helper_control_dict.new(
        {
            "application": "sedFoam_rbgh",
            "startFrom": "latestTime",
            "endTime": 50,
            "deltaT": 0.02,
            "writeFormat": "ascii",
            "writeControl": "adjustableRunTime",
            "writeInterval": 5,
            "adjustTimeStep": "true",
            "maxCo": 0.1,
            "maxAlphaCo": 0.1,
            "maxDeltaT": 1.0,
        }
    )

    _helper_twophase_ras_properties = ConstantFileHelper(
        "twophaseRASProperties",
        {
            "SUS": 3.0,
            "KE1": 0,
            "KE3": 0,
            "B": 0.25,
            "Tpsmall": 1e-6,
        },
        dimensions={"Tpsmall": "kg/m^3/s"},
        default_dimension="",
    )

    # remove these lines to get fluidsimfoam default helpers
    _helper_turbulence_properties = None
    _complete_params_block_mesh_dict = None
