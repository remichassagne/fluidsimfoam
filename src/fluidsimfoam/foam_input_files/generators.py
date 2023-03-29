from abc import ABC, abstractmethod
from inspect import getmodule

import jinja2


class InputFiles:
    """Container of the generator objects"""

    def __init__(self, output):
        self.output = output
        mod = getmodule(type(output.sim))

        loader = jinja2.ChoiceLoader(
            [
                jinja2.PackageLoader(mod.__package__, "templates"),
                jinja2.PackageLoader("fluidsimfoam", "resources"),
            ]
        )

        self.jinja_env = jinja2.Environment(
            loader=loader,
            undefined=jinja2.StrictUndefined,
            keep_trailing_newline=True,
        )

    def get_template(self, template_name):
        return self.jinja_env.get_template(template_name)


class FoamInputFileGenerator(ABC):
    rel_path: str

    def __init__(self, output):
        self.output = output

    def generate_file(self):
        """Generate the file"""
        with open(self.output.sim.path_run / self.rel_path, "w") as file:
            file.write(self.generate_code())

    @abstractmethod
    def generate_code(self):
        """Generate the code of the file"""


class FileGeneratorTemplate(FoamInputFileGenerator):
    template_name: str

    def generate_code(self):
        """Generate the code of the file from the Jinja template"""
        template = self.output.input_files.get_template(self.template_name)
        return template.render(data=self.output.sim.params)


class BlockMeshGeneratorTemplate(FileGeneratorTemplate):
    rel_path = "system/blockMeshDict"
    template_name = "blockMeshDict.jinja"


class BlockMeshGeneratorPython(FoamInputFileGenerator):
    pass
