import argparse
import logging
import os
import random
import sys
import pandas


from duplicategenerator.generate import DuplicateGen
from duplicategenerator import utils
from duplicategenerator import config as cf

# from generate import DuplicateGen
# import utils
# import config as cf


def execute_from_command_line():

    parser = argparse.ArgumentParser(
        prog="Duplicate generator", description="Duplicate generator commmand line tool"
    )

    parser.add_argument("output_file", type=str, help="Name of the output file")

    parser.add_argument(
        "num_originals", type=int, help="Number of original records to be created."
    )

    parser.add_argument(
        "num_duplicates",
        type=int,
        help="Number of duplicate records to be created (maximum number is 9)",
    )

    parser.add_argument(
        "max_duplicate_per_record",
        type=int,
        help="The maximal number of duplicates that can becreated for one original record",
    )

    parser.add_argument(
        "max_modification_per_field",
        type=int,
        help="The maximum number of modifications per field",
    )

    parser.add_argument(
        "max_modification_per_record",
        type=int,
        help="The maximum number of modifications per record",
    )

    parser.add_argument(
        "distribution",
        choices=["uni", "poi", "zip", "uniform", "poisson", "zipf"],
        help="The probability distribution used to create the duplicates (i.e the number of duplicates for one original)",
    )

    parser.add_argument(
        "modification_types",
        type=str,
        choices=["typ", "ocr", "pho", "all"],
        help="Select the modification/error types that will be used when duplicates",
    )

    parser.add_argument(
        "--culture",
        type=str,
        default=None,
        help="Select the country or culture from wich you want demographic data",
    )

    parser.add_argument(
        "--config_file",
        type=str,
        default=None,
        help="Configuration file for the field to be generated",
    )

    args = parser.parse_args()

    dupgen = DuplicateGen(
        int(args.num_originals),
        int(args.num_duplicates),
        int(args.max_duplicate_per_record),
        int(args.max_modification_per_field),
        int(args.max_modification_per_record),
        args.distribution,
        args.modification_types,
        False,  # verbose
        args.culture,
        args.config_file,
        None,
    )  # field_names
    all_records = dupgen.generate(output="dataframe")

    # WRITE CSV OUTPUT
    all_records.to_csv(args.output_file,)


if __name__ == "__main__":
    execute_from_command_line()
