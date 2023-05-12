from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import logging
import math

import subprocess as sb
import re

from metasplit.errors import (
    ReturnCodeError,
    NoSelectionError,
    MissingHeaderError,
    InvalidSelectionError,
)

log = logging.getLogger(__name__)

FILE_VAR_REGEX = re.compile(r"^(.*?)@(.*?)(\?.*?)$")
"""The regex that separates the file path, the id var and the selections"""
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

    @staticmethod
    def consume(string: str) -> tuple[Selection, Optional[str]]:
        """Consume a string and return a Selection + the remaining string"""
        if not (match := SELECTION_GRABBER_REGEX.match(string)):
            raise InvalidSelectionError(
                f"The string {string} cannot be parsed to a selection."
            )

        selection_str: str = match.group(1)
        remaining_str: str = string[len(selection_str) :] or None

        if selection_str.startswith("?") or selection_str.startswith("|"):
            union = UnionSign.POSITIVE
        elif selection_str.startswith("&"):
            union = UnionSign.NEGATIVE
        else:
            raise InvalidSelectionError(
                f"The character {selection_str[0]} cannot be parsed as a selection sign. Valid signs are '?', '|' or '&'"
            )

        selection_str = selection_str[1:]  # remove the sign

        # Now we can parse the selection string
        if "!=" in selection_str:
            sign = SelectionSign.NOT_EQUAL_TO
            pieces = selection_str.split("!=")
        elif "=" in selection_str:
            sign = SelectionSign.EQUAL_TO
            pieces = selection_str.split("=")
        else:
            raise InvalidSelectionError(
                f"Invalid value selection string {selection_str}"
            )

        if pieces[1].startswith("[") and pieces[1].endswith("]"):
            # If this matches, then the selection is of the form
            # [aaa,bbb,...] and we need to unpack it
            packed_values = pieces[1].strip("[]")
            values = packed_values.split(",")
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

    @staticmethod
    def consume_all(string: str) -> tuple[Selection]:
        """Recursively consume a string to obtain all the possible selections from it"""
        selections = []
        while True:
            selection, remainder = Selection.consume(string)
            selections.append(selection)
            if remainder is None:
                return tuple(selections)
            string = remainder


class MetaPath:
    def __init__(self, meta_string: str) -> None:
        matches = FILE_VAR_REGEX.search(meta_string)
        if not matches:
            raise ValueError("Could not match input string. Is it malformed?")
        # This has:
        # Group 1: The file path
        # Group 2: The variable to select
        # Group 3: all the rest of the query

        self.original: str = meta_string

        self.file: Path = Path(matches.group(1)).expanduser().resolve()
        self.selection_var: str = matches.group(2)
        self.selections: tuple[Selection] = Selection.consume_all(matches.group(3))

    def __str__(self) -> str:
        return f"{type(self).__name__} object :: file {self.file} selecting {self.selection_var} on {self.variable} with {self.values}"


def exec(*args, **kwargs) -> str:
    res = sb.run(*args, **kwargs, encoding="UTF-8", capture_output=True, errors="replace")

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

class NumberCompressor:
    def __init__(self) -> None:
        self.compressed = []
        self.expected_number = None
        self.buffer = []
    
    def flush(self):
        if not self.buffer:
            return
        if len(self.buffer) == 1:
            self.compressed.append(f"{self.buffer[0]}")
        else:
            self.compressed.append(f"{min(self.buffer)}-{max(self.buffer)}")
        self.buffer = []

    def gobble(self, i: int) -> None:
        if self.expected_number is None or i == self.expected_number:
            self.expected_number = i+1
            self.buffer.append(i)
            return

        self.flush()
        self.buffer.append(i)
        self.expected_number = i+1


def compress_selection_string(selection: list):
    original_len = len(selection)
    # We can compress the numbers as x-y, while we cannot compress the strings
    numbers = []
    strings = []
    for item in selection:
        try:
            numbers.append(int(item))
        except ValueError:
            strings.append(item)
    
    assert (len(numbers) + len(strings)) == original_len

    compressor = NumberCompressor()
    for i in sorted(numbers):
        compressor.gobble(i)
    compressor.flush()

    compressed = compressor.compressed
    compressed.extend([f'"{x}"' for x in strings])

    rate = round((len(compressed) - original_len) / original_len * 100, 2)
    log.info(f"Compressed selection from {original_len} to {len(compressed)}. Rate: -{rate}%")

    return compressed

def select_meta_ids(metadata: list[MetaPath]) -> list[int]:
    """This function selects the IDs from the metadata files following the MetaPath instructions

    Args:
        metadata (list[MetaPath]): A list of MetaPaths to use

    Raises:
        NoSelectionError: If any MetaPath selects no IDs

    Returns:
        list[str]: The selected IDs from the metadata
    """
    selected_ids = [] # This holds the overall selected indexes, and gets returned

    # Every MetaPath is processed independently of any other.
    for meta in metadata:
        # We now need to:
        # - Find the ID column
        # - Find which indexes to select IDs with based on the selections
        # - Convert from indexes to IDs
        # - Add the IDs to the overall selection
        this_meta_indexes = []
        meta_headers = get_headers(meta.file)
        log.debug(f"Processing {meta.file} - found {len(meta_headers)} headers.")
        # We how have to process the selections, from right to left, in order
        # to select the values in this metadata
        
        for sel in meta.selections:
            # The variable must be in the headers
            log.debug(f"Selecting variable {sel.filter_variable} on values {sel.filter_values}")
            assert (
                sel.filter_variable in meta_headers
            ), f"Variable {sel.filter_variable} not found in metadata headers ({meta_headers})"

            # We can now take out the values for this variable, and convert them
            # to indexes
            var_values = xsv_select(meta.file, sel.filter_variable)
            sel_indexes = indexes_of(var_values, sel.filter_values)
            log.debug(f"Selected {len(sel_indexes)} selection indexes")

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
                log.debug(f"Inverted selection to {len(sel_indexes)} indexes.")
            
            # Now we need to add or remove this selection's indexes to the more
            # generic meta index
            if sel.union is UnionSign.NEGATIVE:
                # we need to remove these from the indexes
                old_len = len(this_meta_indexes)
                this_meta_indexes = [x for x in this_meta_indexes if x in sel_indexes]
                log.debug(f"Negative union: removed {len(this_meta_indexes) - old_len} indexes.")
            elif sel.union is UnionSign.POSITIVE:
                # we need to add these from the indexes
                old_len = len(this_meta_indexes)
                this_meta_indexes.extend(sel_indexes)
                this_meta_indexes = list(set(this_meta_indexes))  # remove duplicates
                log.debug(f"Positive union: added {len(this_meta_indexes) - old_len} indexes")
            
        # When we get here, the indexes are correct, and we parsed all selections
        # We now have to convert from the indexes to the IDs
        # We always add here.
        meta_ids = xsv_select(meta.file, meta.selection_var)
        selected_ids.extend([meta_ids[i] for i in this_meta_indexes])
    
    # After parsing all selections, we just return.
    log.debug(f"Returning {len(selected_ids)} ids")
    return selected_ids


def metasplit(
    metadata: list[MetaPath],
    input_file: Path,
    output_file: Path,
    ignore_missing: bool = False,
    input_delimiter: str = ",",
    always_include: Optional[list[str]] = None,
) -> None:
    if not input_file.exists():
        raise ValueError(f"Input csv {input_file} does not exist.")

    target_headers = get_headers(input_file, input_delimiter)

    # We can now select the columns of interest
    selected_ids = select_meta_ids(metadata)
    
    # We now have our Ids. We have to check if they are all in the
    # target file and discard them if we are told to ignore the missing IDs
    if ignore_missing:
        selected_ids = [id for id in selected_ids if id in target_headers]
    
    if always_include:
        selected_ids.extend(always_include)
        selected_ids = list(dict.fromkeys(selected_ids))

    # For compactness, we have to go back to 1-based column indexes, so our
    # xsv calls do not exceed the max command len imposed by bash.
    SELECTIONS = [x + 1 for x in indexes_of(target_headers, selected_ids)]

    # We're done. We just need to pass these selections to XSV

    log.info(f"Selecting {len(SELECTIONS)} results...")
    # Compress the IDs further...
    SELECTIONS = compress_selection_string(SELECTIONS)
    selection_str = ",".join(SELECTIONS)
    xsv_select(
        input_file,
        selection_str,
        input_delimiter,
        include_header=True,
        output_file=output_file,
    )

    print("Done!")

