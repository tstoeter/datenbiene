#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import pandas as pd
import logging
import argparse
import json
from jinja2 import Template
from sources import *
from sinks import *
from checkers import *


__author__ = "Torsten Stöter"
__copyright__ = "Copyright 2025 " + __author__
__license__ = "GPL-3.0-only"
__version__ = "1.0"


logger = logging.getLogger(__name__)


def str_to_class(classname):
    return getattr(sys.modules[__name__], classname)


def cli(args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-e",
        "--excel",
        required=True,
        help="Path to the Excel file containing Sources and Sinks sheets.",
    )
    parser.add_argument(
        "-j",
        "--json",
        required=True,
        help="Path to the JSON file containing key-value pairs.",
    )
    args = parser.parse_args(args)

    sources_df = pd.read_excel(args.excel, "Sources")
    checkers_df = pd.read_excel(args.excel, "Checkers")
    sinks_df = pd.read_excel(args.excel, "Sinks")

    with open(args.json) as f:
        keyvals = json.load(f)
    print(keyvals)

    return sources_df, checkers_df, sinks_df, keyvals


def main(sources_df, checkers_df, sinks_df, keyvals):

    # apply Jinja2 template rendering to every cell using key-value pairs
    sources_df = sources_df.map(
        lambda x: Template(x).render(keyvals) if not pd.isnull(x) else x
    )
    print(sources_df)
    sinks_df = sinks_df.map(
        lambda x: Template(x).render(keyvals) if not pd.isnull(x) else x
    )
    print(sinks_df)

    # process all sources
    sources = []
    for idx, row in sources_df.iterrows():

        if pd.isnull(row["Source"]):
            continue

        try:
            CS = str_to_class(row["Source"] + "Source")
        except AttributeError:  # class not found, use generic source
            CS = GenericSource

        addopt = (
            json.loads(row["AdditionalOptions"])
            if not pd.isnull(row["AdditionalOptions"])
            else {}
        )
        path_patterns = (
            row["PathPatterns"].split(";") if not pd.isnull(row["PathPatterns"]) else []
        )
        file_patterns = (
            row["FilePatterns"].split(";") if not pd.isnull(row["FilePatterns"]) else []
        )
        src = CS(row["Name"], path_patterns, file_patterns, keyvals | addopt)

        print(src.get_filelist())
        sources.append(src)

    # run all checkers
    # TODO

    # process all sinks
    for idx, row in sinks_df.iterrows():
        print(row)
        if pd.isnull(row["Sink"]):
            continue

        try:
            CS = str_to_class(row["Sink"] + "Sink")
        except AttributeError:  # class not found, use generic source
            CS = Sink

        snk = CS(row["Target"], sources, keyvals)
        sources = snk.store()


if __name__ == "__main__":
    inputs = cli(sys.argv[1:])
    main(*inputs)
