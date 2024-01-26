#! python3  # noqa: E265

"""
    Read YAML files produced by Isogeo Scan.

    See:

    - https://docs.python.org/fr/3/library/YAML file.html

"""


# #############################################################################
# ########## Libraries #############
# ##################################
# standard library
import logging
from collections.abc import Generator
from io import BufferedIOBase
from os import R_OK, access
from pathlib import Path
from typing import Union

# 3rd party
import yaml

# submodule
from scan_offline.explorer.formats_matrix import FormatMatcher

# #############################################################################
# ########## Globals ###############
# ##################################

logger = logging.getLogger(__name__)


# ##############################################################################
# ########## Classes ###############
# ##################################
class FormatYamlReader:
    """Read a YAML file specifying a format configuration.

    :param in_yaml: path to the yaml file to read.
    """

    model = dict
    format_definition = dict

    def __init__(self, in_yaml: Union[str, Path, BufferedIOBase]):
        """Instanciating Isogeo Metadata YAML Reader."""
        # check and get YAML path
        if isinstance(in_yaml, (str, Path)):
            self.input_yaml = self.check_yaml_file(in_yaml)
            # extract data from input file
            with self.input_yaml.open(mode="r") as bytes_data:
                self.model, self.format_definition = self.check_yaml_structure(
                    yaml.full_load_all(bytes_data)
                )
        elif isinstance(in_yaml, BufferedIOBase):
            self.input_yaml = self.check_yaml_buffer(in_yaml)
            # extract data from input file
            self.model, self.format_definition = self.check_yaml_structure(
                yaml.full_load_all(self.input_yaml)
            )
        else:
            raise TypeError

    # CHECKS
    def check_yaml_file(self, yaml_path: Union[str, Path]) -> Path:
        """Perform some checks on passed yaml file and load it as Path object.

        :param yaml_path: path to the yaml file to check

        :returns: sanitized yaml path
        :rtype: Path
        """
        # if path as string load it in Path object
        if isinstance(yaml_path, str):
            try:
                yaml_path = Path(yaml_path)
            except Exception as exc:
                raise TypeError(f"Converting yaml path failed: {exc}")

        # check if file exists
        if not yaml_path.exists():
            raise FileExistsError(
                f"YAML file to check doesn't exist: {yaml_path.resolve()}"
            )

        # check if it's a file
        if not yaml_path.is_file():
            raise OSError(f"YAML file is not a file: {yaml_path.resolve()}")

        # check if file is readable
        if not access(yaml_path, R_OK):
            raise OSError(f"yaml file isn't readable: {yaml_path}")

        # check integrity and structure
        with yaml_path.open(mode="r") as in_yaml_file:
            try:
                yaml.safe_load_all(in_yaml_file)
            except yaml.YAMLError as exc:
                logger.error(msg=f"YAML file is invalid: {yaml_path.resolve()}")
                raise exc
            except Exception as exc:
                logger.error(msg=f"Structure of YAML file is incorrect: {exc}")
                raise exc

        # return sanitized path
        return yaml_path

    def check_yaml_buffer(self, yaml_buffer: BufferedIOBase) -> BufferedIOBase:
        """Perform some checks on passed yaml file.

        :param yaml_buffer: bytes reader of the yaml file to check

        :returns: checked bytes object
        :rtype: BufferedIOBase
        """
        # check integrity
        try:
            yaml.safe_load_all(yaml_buffer)
        except yaml.YAMLError as exc:
            logger.error(f"Invalid YAML {yaml_buffer}. Trace: {exc}")
            raise exc

        # return sanitized path
        return yaml_buffer

    def check_yaml_structure(self, in_yaml_data: Generator) -> tuple:
        """Look into the YAML structure and check everything it's OK. \
            Two documents are expected to be found into the YAML file.

        :param Generator in_yaml_data: [description]

        :return: tuple of 2 dicts
        :rtype: tuple

        :example:

        .. code-block:: python

            # here comes an example in Python
            my_yaml = Path("format_sample.yml")
            with my_yaml.open(mode="r") as op:
                yaml_data = yaml.full_load_all(bytes_data)
                model, format_definition = check_yaml_structure(yaml_data)
        """
        # convert generator into list to parse content
        li_docs = list(in_yaml_data)

        # check root structure
        assert isinstance(li_docs, list)
        assert len(li_docs) == 1
        assert isinstance(li_docs[0], dict)

        # check dict of dicts
        docs = li_docs[0]
        assert "model" in docs
        assert docs.get("model").get("type") == "format"
        assert "format" in docs

        # return list of docs as dictionaries
        return docs.get("model"), docs.get("format")

    # PROPERTIES
    @property
    def as_format_matcher(self) -> FormatMatcher:
        """Load YAML into a FormatMatcher (named tuple).

        :return: format named tuple
        :rtype: FormatMatcher
        """
        return FormatMatcher(**self.format_definition)


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # logger.setLevel(logging.INFO)
    fixtures_dir = Path("./tests/fixtures/")

    for i in fixtures_dir.glob("**/*.y*ml"):
        # testing with a Path
        print(type(i), isinstance(i, Path))
        t = FormatYamlReader(i)
        print(isinstance(t.model, dict))
        print(isinstance(t.format_definition, dict))
        print(isinstance(t.as_format_matcher, FormatMatcher))

        # testing with a bytes object
        with i.open("rb") as in_yaml:
            print(type(in_yaml), isinstance(in_yaml, BufferedIOBase))
            t = FormatYamlReader(in_yaml)
            print(isinstance(t.model, dict))
            print(isinstance(t.format_definition, dict))
            print(isinstance(t.as_format_matcher, FormatMatcher))
