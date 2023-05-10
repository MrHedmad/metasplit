from pathlib import Path

from metasplit.core import metasplit, MetaPath


def main():
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "selection_string", type=str, nargs="+", help="Selection string(s). Read the README for a guide on how to write these."
    )
    parser.add_argument("input_csv", type=Path, help="The csv to subset with the metadata.")
    parser.add_argument("output_csv", type=Path, help="The file to save the subsetted data in.")
    parser.add_argument(
        "--ignore_missing",
        action="store_true",
        help="If set, ignore IDs selected by the metadata that are not in the target csv to subset.",
    )
    parser.add_argument(
        "--input_delimiter",
        type=str,
        default=",",
        help="The delimiter to use in the input file.",
    )
    parser.add_argument(
        "--always_include",
        type=str,
        default=None,
        help="A comma-separated list of columns to always include in the output.",
    )

    args = parser.parse_args()

    always_include = args.always_include.split(",") if args.always_include else None

    metasplit(
        metadata=[MetaPath(x) for x in args.selection_string],
        input_file=args.input_csv,
        output_file=args.output_csv,
        ignore_missing=args.ignore_missing,
        input_delimiter=args.input_delimiter,
        always_include=always_include
    )
