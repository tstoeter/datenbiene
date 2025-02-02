#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tarfile
import hashlib
import filetype
import owncloud
import smtplib
from email.message import EmailMessage
from config import config
from sources import Source


class Sink:
    def __init__(self, target, sources, additional_options=None):
        self.target = target
        self.sources = sources

    def store(self):
        return self.sources


class TarballSink(Sink):
    def __init__(self, target, sources, additional_options):
        super().__init__(target, sources, additional_options)

        self.subject = additional_options["subject"].lower()
        # date string should be in format 20250124: here we strip all non-digits
        self.date = int(
            "".join([c for c in str(additional_options["date"]) if c.isdigit()])
        )
        self.study = additional_options["study"]

        self.prefix = f"{self.subject}_{self.date}"

    def store(self):

        if not os.path.isdir(self.target):
            os.mkdir(self.target)

        session_dir = os.path.join(self.target, self.prefix)
        os.mkdir(session_dir)

        tarfiles = []

        for src in self.sources:
            print(src.name)
            filelist = src.get_filelist()
            compress = 9

            # disbale compression for videos
            if "video" in src.name.lower():
                compress = 0
            for f in filelist:
                if not os.path.isfile(f):
                    continue
                kind = filetype.guess(f)
                print(f, kind)
                if kind and "video" in kind.mime:
                    compress = 0

            tarfilename = os.path.join(
                session_dir, self.prefix + "_" + src.name + ".tar.gz"
            )

            tar = tarfile.open(tarfilename, "w:gz", compresslevel=compress)

            for f in src.get_filelist():
                print(f"Storing {f} to {tar} ...")
                tar.add(f, arcname=os.path.basename(f))
            tar.close()

            tarfiles.append(tarfilename)

        print("Computing checksums for ", tarfiles)

        hashlines = []
        for tf in tarfiles:
            with open(tf, "rb") as f:
                digest = hashlib.file_digest(f, "sha256").hexdigest()
                hashlines.append(f"SHA256 ({os.path.basename(tf)}) = {digest}\n")

        checksum_file = os.path.join(session_dir, self.prefix + "_Checksums.txt")
        with open(checksum_file, "w") as f:
            f.writelines(hashlines)

        tarfiles.append(checksum_file)

        return [Source("TarballSink", [session_dir], tarfiles)]


class NextcloudSink(Sink):
    def __init__(self, target, sources, additional_options=None):
        super().__init__(target, sources, additional_options)

    def store(self):
        print("Uploading to NexCloud: " + self.target)

        oc = owncloud.Client.from_public_link(self.target)
        for src in self.sources:
            for f in src.get_filelist():
                print("Uploading... " + f)
                oc.put_file("/" + os.path.basename(f), f, chunked=False)

        return self.sources


class EmailSink(Sink):
    def __init__(self, target, sources, additional_options=None):
        super().__init__(target, sources, additional_options)

        self.subject = additional_options["subject"].lower()
        # date string should be in format 20250124: here we strip all non-digits
        self.date = int(
            "".join([c for c in str(additional_options["date"]) if c.isdigit()])
        )
        self.study = additional_options["study"]

    def store(self):
        msg = EmailMessage()
        msg.set_content("Hello World!")
        msg["Subject"] = (
            "Datenbiene: " + self.study + " " + self.subject + " " + str(self.date)
        )
        msg["From"] = config["MailServerFrom"]
        msg["To"] = self.target

        # send the message via our own SMTP server
        s = smtplib.SMTP(config["MailServerHost"], port=config["MailServerPort"])
        s.send_message(msg)
        s.quit()

        return self.sources


class OmeroSink(Sink):
    pass


class BidsSink(Sink):
    pass
