from pathlib import Path

from metasplit import MetaPath
from metasplit.core import metasplit


def main():
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "selection_string", type=str, nargs="+", help="Selection string(s)"
    )
    parser.add_argument("input_csv", type=Path, help="csv to process")
    parser.add_argument("output_csv", type=Path, help="output csv")
    parser.add_argument(
        "--ignore_missing",
        action="store_true",
        help="If set, ignore IDs in the metadata not in the target csv to subset",
    )
    parser.add_argument(
        "--input_delimiter",
        type=str,
        default=",",
        help="The delimiter to use in the input file",
    )

    args = parser.parse_args()

    metasplit(
        metadata=[MetaPath(x) for x in args.metadata],
        input_file=args.input_csv,
        output_file=args.output_csv,
        ignore_missing=args.ignore_missing,
        input_delimiter=args.input_delimiter,
    )
