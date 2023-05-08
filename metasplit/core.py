from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import logging

import subprocess as sb
import re

from metasplit.errors import (
    ReturnCodeError,
    NoSelectionError,
    MissingHeaderError,
    InvalidSelectionError,
)

log = logging.getLogger(__name__)

FILE_VAR_REGEX = re.compile(r"^(.*?)@(.*?)\?(.*?)$")
"""The regex that separates the file path, the id var and the selections"""
SELECTION_VALUES_REGEX = re.compile(r"\[(.*?)(?:,(.*?))*\]")
"""The regex that separates the lists of values to parse"""
SELECTION_GRABBER_REGEX = re.compile(r"([?&\|].+?)(?:[?&\|]|$)")
"""This regex can match the start of a selection in order to consume it"""


class UnionSign(Enum):
    """An enum that enumerates the possible signs that a selection may have"""

    POSITIVE = "+"
    NEGATIVE = "-"


class SelectionSign(Enum):
    """An enum that represents possible signs that values can take"""

    EQUAL_TO = "="
    NOT_EQUAL_TO = "!="


@dataclass
class Selection:
    """This class represents one of the selection expressions in the query"""

    filter_variable: str
    """The variable to filter by"""
    sign: SelectionSign
    """The sign of the selection, either equal to or not equal to"""
    union: UnionSign
    """The type of union to determine how to merge with other IDS (AND, -) or (OR, +)"""
    filter_values: list[str]
    """The values to filter by"""

    @classmethod
    def consume(string: str) -> tuple(Selection, Optional[str]):
        """Consume a string and return a Selection + the remaining string"""
        if not (match := SELECTION_GRABBER_REGEX):
            raise InvalidSelectionError(
                f"The string {string} cannot be parsed to a selection."
            )

        selection_str: str = match.group(1)
        remaining_str: str = string[len(selection_str) :] or None

        if selection_str.startswith("?") or selection_str.startswith("|"):
            union = SelectionSign.POSITIVE
        elif selection_str.startswith("&"):
            union = SelectionSign.NEGATIVE
        else:
            raise InvalidSelectionError(
                f"The character {selection_str[0]} cannot be parsed as a selection sign. Valid signs are '?', '|' or '&'"
            )

        selection_str = selection_str[1:]  # remove the sign

        # Now we can parse the selection string
        if "!=" in selection_str:
            sign = UnionSign.NOT_EQUAL_TO
            pieces = selection_str.split("!=")
        elif "=" in selection_str:
            sign = UnionSign.EQUAL_TO
            pieces = selection_str.split("=")
        else:
            raise InvalidSelectionError(
                f"Invalid value selection string {selection_str}"
            )

        if match := SELECTION_VALUES_REGEX.match(pieces[1]):
            # If this matches, then the selection is of the form
            # [aaa,bbb,...] and we need to unpack it
            values = [x for x in match.groups() if x is not None]
        else:
            # If that did not match, then we consider this as just one
            # selection
            values = [pieces[1]]

        return (
            Selection(
                filter_variable=pieces[0],
                sign=sign,
                union=union,
                filter_values=values,
            ),
            remaining_str,
        )

    @classmethod
    def consume_all(string: str) -> tuple(Selection):
        """Recursively consume a string to obtain all the possible selections from it"""
        selections = []
        while True:
            selection, remainder = MetaPath.consume(string)
            selections.append(selection)
            if remainder is None:
                return tuple(selections)
            string = selection


class MetaPath:
    def __init__(self, meta_string: str) -> None:
        matches = FILE_VAR_REGEX.search(meta_string)
        if not matches:
            raise ValueError("Could not match input string. Is it malformed?")
        # This has:
        # Group 1: The file path
        # Group 2: The variable to select
        # Group 3: all the rest of the query (except the first ?)

        self.original: str = meta_string

        self.file: Path = Path(matches.group(1)).expanduser().resolve()
        assert self.file.exists(), f"File {self.file} not found."
        self.selection_var: str = matches.group(2)
        self.selections: tuple[Selection] = Selection.consume_all(matches.group(3))

        ## Validity checks
        headers = exec(["xsv", "headers", "-j", self.file]).split("\n")
        assert (
            self.variable in headers
        ), f"Header {self.variable} not in metadata headers"

    def __str__(self) -> str:
        return f"{type(self).__name__} object :: file {self.file} selecting {self.selection_var} on {self.variable} with {self.values}"


def exec(*args, **kwargs) -> str:
    res = sb.run(*args, **kwargs, encoding="UTF-8", capture_output=True)

    if res.returncode != 0:
        raise ReturnCodeError(
            f"Process exited with code {res.returncode}:\n{res.stderr}"
        )

    return res.stdout.strip()


def xsv_select(
    file: Path,
    var: str,
    delim: str = ",",
    include_header: bool = False,
    output_file: Optional[Path] = None,
) -> list(str):
    assert file.exists(), f"Cannot run xsv on file {file} that does not exist"

    command = ["xsv", "select", "-d", delim, var, file]
    if output_file:
        command.extend(["-o", output_file])
    values: list[str] = exec(command).split("\n")
    if not include_header:
        values.pop(0)

    return values


def get_headers(file: Path, delimiter: str = ","):
    return exec(["xsv", "headers", "-j", "-d", delimiter, file]).split("\n")


def indexes_of(list: list[str], selection: list[str]) -> list[int]:
    return [i for i, x in enumerate(list) if x in selection]


def invert_index(list_len: int, indexes: list[int]) -> list[int]:
    return [i for i in range(list_len) if i not in indexes]


def metasplit(
    metadata: list[MetaPath],
    input_file: Path,
    output_file: Path,
    ignore_missing: bool = False,
    input_delimiter: str = ",",
) -> None:
    assert input_file.exists(), f"Input csv {input_file} does not exist."

    SELECTION_COLNAMES = []
    # We can now select the columns of interest
    for meta in metadata:
        meta_headers = get_headers(meta.file)
        log.info(f"Processing {meta.file} - found {len(meta_headers)} headers.")

        # We how have to process the selections, from right to left, in order
        # to select the values in this metadata
        indexes = []
        for sel in meta.selections:
            assert (
                sel.filter_variable in meta_headers
            ), f"Variable {sel.filter_variable} not found in metadata headers"
            var_values = xsv_select(meta.file, sel.filter_variable)
            sel_indexes = indexes_of(var_values, sel.filter_values)
            if not sel_indexes:
                raise NoSelectionError(
                    f"Variable {sel.filter_variable} has no selection in {sel.filter_values}"
                )
            # Ok, we now have the indexes of this selection.
            # If the selection was negative (!=) we need to select the opposite
            # though, and this is what we do here:
            if sel.sign is SelectionSign.NOT_EQUAL_TO:
                sel_indexes = invert_index(
                    len(var_values), sel_indexes
                )  # We need to select every OTHER index
            # Now we need to add or remove the selection indexes to the overall index
            if sel.union is UnionSign.NEGATIVE:
                # we need to remove these from the indexes
                indexes = [x for x in indexes if x not in sel_indexes]
            elif sel.union is UnionSign.POSITIVE:
                # we need to add these from the indexes
                indexes.extend(sel_indexes)
                indexes = list(set(indexes))  # remove duplicates

    # We now have our indexes. select the columns with the indexes
    headers = get_headers(input_file, input_delimiter)
    SELECTION_COLNAMES = headers[indexes]

    if not SELECTION_COLNAMES:
        raise NoSelectionError("Nothing was selected by the metadata directives")

    target_headers = get_headers(input_file, input_delimiter)
    log.info(f"Target has {len(target_headers)} columns.")

    if ignore_missing:
        SELECTION_COLNAMES = [x for x in SELECTION_COLNAMES if x in target_headers]

        if not SELECTION_COLNAMES:
            raise NoSelectionError("Nothing survived after removing missing headers")
    else:
        if any([x not in target_headers for x in SELECTION_COLNAMES]):
            raise MissingHeaderError(
                "Some metadata selected headers are not in the subsetted matrix"
            )

    print(f"Selecting {len(SELECTION_COLNAMES)} results...")
    selection_str = ",".join([f'"{x}"' for x in SELECTION_COLNAMES])
    xsv_select(
        input_file,
        selection_str,
        input_delimiter,
        include_header=True,
        output_file=output_file,
    )

    print("Done!")
