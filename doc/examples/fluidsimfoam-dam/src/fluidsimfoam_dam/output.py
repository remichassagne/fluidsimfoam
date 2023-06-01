from fluidsimfoam.foam_input_files import BlockMeshDict, ConstantFileHelper
from fluidsimfoam.output import Output


class OutputDam(Output):
    name_variables = ["U", "alpha.water", "p_rgh"]
    name_system_files = [
        "blockMeshDict",
        "controlDict",
        "decomposeParDict",
        "fvSchemes",
        "fvSolution",
        "sampling",
        "setFieldsDict",
    ]
    name_constant_files = ["g", "transportProperties", "turbulenceProperties"]

    _helper_control_dict = Output._helper_control_dict.new(
        """
        application     interFoam
        endTime         1
        deltaT          0.001
        writeControl    adjustable
        writeInterval   0.05
        adjustTimeStep  true
        maxCo           1
        maxAlphaCo      1
        maxDeltaT       1
    """
    )

    _helper_control_dict.include_function('"sampling"', kind="#sinclude")

    _helper_transport_properties = ConstantFileHelper(
        "transportProperties",
        {
            "phases": ["water", "air"],
            "water": {
                "transportModel": "Newtonian",
                "nu": 1e-06,
                "rho": 1000,
            },
            "air": {
                "transportModel": "Newtonian",
                "nu": 1.48e-05,
                "rho": 1,
            },
            "sigma": 0.07,
        },
    )