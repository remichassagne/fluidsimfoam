"""
To see the coverage, run as:

```
pytest tests/test_blockmeshhelper.py -vv --cov --cov-report term --cov-report html
firefox htmlcov/index.html
```
"""

import math
from pathlib import Path

import pytest

from fluidsimfoam.foam_input_files import dump, parse
from fluidsimfoam.foam_input_files.blockmeshhelper import (
    ArcEdge,
    BlockMeshDict,
    EdgeGrading,
    Point,
    SimpleGrading,
    SplineEdge,
    Vertex,
)


def create_code_example():
    wedgedegree = 5.0

    # geometries
    radius_x = 0.19
    length_z = 1.1

    # prepare ofblockmeshdicthelper.BlockMeshDict instance to
    # gather vertices, blocks, faces and boundaries.
    bmd = BlockMeshDict()

    # set metrics
    bmd.set_metric("m")

    # base vertices which are rotated +- 2.5 degrees
    basevs = [
        Vertex(0, 0, 0, "v0"),
        Vertex(radius_x, 0, 0, "v1"),
        Vertex(radius_x, 0, length_z, "v2"),
        Vertex(0, 0, length_z, "v3"),
    ]

    # rotate wedgedegree/2 around z axis
    # rotated vertices are named with '-y' or '+y' suffix.
    # these verteces are added to BlockMeshDict instence to be referred
    # by following blocks and faces...
    cosd = math.cos(math.radians(wedgedegree / 2.0))
    sind = math.sin(math.radians(wedgedegree / 2.0))
    for v in basevs:
        bmd.add_vertex(v.x * cosd, -v.x * sind, v.z, v.name + "-y")
        bmd.add_vertex(v.x * cosd, v.x * sind, v.z, v.name + "+y")

    # v0+y and v3+y have same coordinate as v0-y and v3-y, respectively.
    bmd.reduce_vertex("v0-y", "v0+y")
    bmd.reduce_vertex("v3-y", "v3+y")

    def vnamegen(x0z0, x1z0, x1z1, x0z1):
        return (
            x0z0 + "-y",
            x1z0 + "-y",
            x1z0 + "+y",
            x0z0 + "+y",
            x0z1 + "-y",
            x1z1 + "-y",
            x1z1 + "+y",
            x0z1 + "+y",
        )

    b0 = bmd.add_hexblock(
        vnamegen("v0", "v1", "v2", "v3"),
        (19, 1, 300),
        "b0",
        grading=SimpleGrading(
            0.1, ((0.2, 0.3, 4), (0.6, 0.4, 1), (0.2, 0.3, 1.0 / 4.0)), 1
        ),
    )

    # face element of block can be generated by Block.face method
    bmd.add_boundary("wedge", "front", [b0.face("s")])
    bmd.add_boundary("wedge", "back", [b0.face("n")])
    bmd.add_boundary("wall", "tankWall", [b0.face("e")])
    bmd.add_boundary("patch", "inlet", [b0.face("b")])
    bmd.add_boundary("patch", "outlet", [b0.face("t")])
    bmd.add_boundary("empty", "axis", [b0.face("w")])

    # TODO: we need to improve the API by avoiding this call
    # prepare for output
    bmd.assign_vertexid()

    return bmd.format()


def create_code_cbox():
    num_mesh_x = 80
    num_mesh_y = 80
    # geometries
    length_x = 1.0
    length_y = 1.0
    length_z = 0.1

    bmd = BlockMeshDict()

    bmd.set_metric("m")

    basevs = [
        Vertex(0, 0, length_z, "v0"),
        Vertex(length_x, 0, length_z, "v1"),
        Vertex(length_x, length_y, length_z, "v2"),
        Vertex(0, length_y, length_z, "v3"),
    ]

    for v in basevs:
        bmd.add_vertex(v.x, v.y, 0, v.name + "-0")
        bmd.add_vertex(v.x, v.y, v.z, v.name + "+z")

    # utility to to generate vertex names
    def vnamegen(x0z0, x1y0, x1y1, x0z1):
        return (
            x0z0 + "-0",
            x1y0 + "-0",
            x1y1 + "-0",
            x0z1 + "-0",
            x0z0 + "+z",
            x1y0 + "+z",
            x1y1 + "+z",
            x0z1 + "+z",
        )

    # Noted that 'v0+y' and 'v3+y' are still valid
    b0 = bmd.add_hexblock(
        vnamegen("v0", "v1", "v2", "v3"),
        (num_mesh_x, num_mesh_y, 1),
        "",
    )

    # face element of block can be generated by Block.face method
    bmd.add_boundary("wall", "frontAndBack", [b0.face("s"), b0.face("n")])
    bmd.add_boundary("wall", "topAndBottom", [b0.face("t"), b0.face("b")])
    bmd.add_boundary("wall", "hot", [b0.face("e")])
    bmd.add_boundary("wall", "cold", [b0.face("w")])

    # prepare for output
    bmd.assign_vertexid(sort=False)

    return bmd.format()


path_data = Path(__file__).absolute().parent / "data_blockmeshhelper"


@pytest.mark.parametrize(
    "name",
    ["example", "cbox"],
)
def test_blockmesh(name):
    create_blockmesh = globals()["create_code_" + name]
    code_from_py = create_blockmesh()

    if name == "cbox":
        path_saved_file = (
            path_data.parent
            / "pure_openfoam_cases/cbox/sim0/system/blockMeshDict"
        )
        with open(path_data / ("blockmesh_" + name), "w") as file:
            file.write(code_from_py)
    else:
        path_saved_file = path_data / ("blockmesh_" + name)

    code_saved = path_saved_file.read_text()

    tree_saved_file = parse(code_saved)
    tree_from_py = parse(code_from_py)

    assert dump(tree_saved_file).strip() == dump(tree_from_py).strip()


def test_edge_grading():
    eg = EdgeGrading(*list(range(12)))
    assert eg.format() == "edgeGrading (0 1 2 3 4 5 6 7 8 9 10 11)"


def test_arc_edge():
    vertices = {
        name: Vertex(index * 0.1, index * 0.2, index * 0.3, name, index=index)
        for index, name in enumerate("abc")
    }
    edge = ArcEdge(list("abc"), "edgename", vertices["b"])
    assert (
        edge.format(vertices)
        == "arc 0 1 2 (               0.1                0.2                0.3) // edgename (a b c)"
    )


def test_spline_edge():
    vertices = {
        name: Vertex(index * 0.1, index * 0.2, index * 0.3, name, index=index)
        for index, name in enumerate("abc")
    }
    edge = SplineEdge(
        list("abc"), "edgename", [Point(0.1, 0.1, 0.1), Point(0.2, 0.2, 0.2)]
    )
    assert (
        edge.format(vertices)
        == """spline 0 1 2                      // edgename (a b c)
    (
         (                0.1                0.1                0.1 )
         (                0.2                0.2                0.2 )
)"""
    )
