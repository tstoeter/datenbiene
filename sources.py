#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import tempfile
from rspace_client.eln import eln
import pdfkit
import shutil
from citric import Client
import io
import pandas as pd
from pydicom import dcmread
from config import secrets


class Source:
    def __init__(self, name, path_patterns, filename_patterns, additional_options=None):
        self.name = name
        self.path_patterns = path_patterns
        self.filename_patterns = filename_patterns
        self.filelist_cache = None

    # hook for preprocessing, e.g. for downloading files from remote sources
    def pre_hook(self):
        return

    def get_filelist(self):
        # do nothing if filelist was already created
        if self.filelist_cache:
            return self.filelist_cache

        self.pre_hook()

        filelist = []

        for pp in self.path_patterns:
            for fp in self.filename_patterns:
                filelist += glob.glob(os.path.join(pp, fp))

        return self.post_hook(filelist)

    # hook for postprocessing, e.g. for filtering the file list
    def post_hook(self, filelist):
        return filelist


class GenericSource(Source):
    pass


class RspaceSource(Source):
    def __init__(self, name, path_patterns, filename_patterns, additional_options=None):
        super().__init__(name, path_patterns, filename_patterns, additional_options)

        self.urls = path_patterns
        self.search_docs = additional_options["search_docs"]

        self.path_patterns = [tempfile.mkdtemp()]
        self.filename_patterns = ["*.pdf", "*.zip"]

    # Export and download RSpace documents, and store results in temp directory
    def pre_hook(self):
        # do nothing if filelist was already created
        if self.filelist_cache:
            return

        client = eln.ELNClient(self.urls[0], secrets["RspaceApiKey"])
        res = client.get_documents()
        documents = res["documents"]

        while client.link_exists(res, "next"):
            res = client.get_link_contents(res, "next")
            documents += res["documents"]

        filtered_ids = [
            doc["id"] for doc in documents if self.search_docs in doc["name"]
        ]

        filename = os.path.join(
            self.path_patterns[0], self.search_docs + "_" + self.name
        )
        client.download_export_selection("html", filename + ".zip", filtered_ids)
        shutil.unpack_archive(filename + ".zip", self.path_patterns[0])

        files = glob.glob(self.path_patterns[0] + "/**/*.html", recursive=True)
        html_str = ""
        for i, fname in enumerate(files):
            with open(fname, "r") as f:
                html_str += "".join(f.readlines())
            if i < len(files) - 1:
                html_str += '<div style="float: none;"><div style="page-break-after: always;"></div></div>'  # page breaks between documents

        # change relative to absolute paths in order to find css
        html_str = html_str.replace(
            "../resources/", self.path_patterns[0] + "/resources/"
        )
        html_str = html_str.replace(
            "./resources/", self.path_patterns[0] + "/resources/"
        )
        html_str = html_str.replace(
            '"resources/', '"' + self.path_patterns[0] + "/resources/"
        )

        with open(filename + ".html", "w") as html_file:
            html_file.write(html_str)

        opts = {"enable-local-file-access": None}
        pdfkit.from_string(html_str, filename + ".pdf", options=opts)


class LimesurveySource(Source):
    def __init__(self, name, path_patterns, filename_patterns, additional_options):
        super().__init__(name, path_patterns, filename_patterns, additional_options)

        self.urls = path_patterns
        self.survey_ids = additional_options["survey_ids"]
        self.subject = additional_options["subject"]

        self.path_patterns = [tempfile.mkdtemp()]
        self.filename_patterns = ["*.xlsx"]

    # Export and download LimeSurvey results, and store results in temp directory
    def pre_hook(self):
        # do nothing if filelist was already created
        if self.filelist_cache:
            return

        # Connect to your LimeSurvey instance
        client = Client(
            self.urls[0], secrets["LimesurveyUser"], secrets["LimesurveyPassword"]
        )

        # fetch survey responses
        for survey in client.list_surveys():
            for sid in self.survey_ids:
                if sid == int(survey["sid"]):
                    survey_title = survey["surveyls_title"]

                    # Export responses to CSV and read into a Pandas DataFrame
                    df = pd.read_csv(
                        io.BytesIO(client.export_responses(sid, file_format="csv")),
                        delimiter=";",
                        index_col="id",
                    )

                    df2 = df.loc[df["subj"] == self.subject]
                    title = (
                        "".join(
                            c
                            for c in survey_title
                            if c.isalpha() or c.isdigit() or c == " "
                        )
                        .rstrip()
                        .replace(" ", "-")
                    )
                    filename = os.path.join(
                        self.path_patterns[0],
                        self.subject + "_" + title + "_questions.xlsx",
                    )
                    df2.to_excel(filename)


class MriSource(Source):
    def __init__(self, name, path_patterns, filename_patterns, additional_options):
        super().__init__(name, path_patterns, filename_patterns, additional_options)

        self.subject = additional_options["subject"].lower()
        # date string should be in format 20250124: here we strip all non-digits
        self.date = int(
            "".join([c for c in str(additional_options["date"]) if c.isdigit()])
        )
        self.study = additional_options["study"].lower()

    def post_hook(self, filelist):

        filtered_filelist = []

        for p in filelist:

            first_dcmfile = glob.glob(os.path.join(p, "MR*"))[0]
            ds = dcmread(first_dcmfile)

            if (
                self.subject in ds.PatientID.lower()
                and self.date == int(ds.AcquisitionDate)
                and self.study in ds.StudyDescription.lower()
            ):
                filtered_filelist.append(p)

        return filtered_filelist
