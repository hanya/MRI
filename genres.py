#! /usr/bin/env python

import os, os.path

desc_h = """<?xml version='1.0' encoding='UTF-8'?>
<description xmlns="http://openoffice.org/extensions/description/2006"
xmlns:xlink="http://www.w3.org/1999/xlink"
xmlns:d="http://openoffice.org/extensions/description/2006">
<identifier value="mytools.mri" />
<version value="{VERSION}" />
<dependencies>
<OpenOffice.org-minimal-version value="3.4" d:name="OpenOffice.org 3.4" />
</dependencies>
<registration>
<simple-license accept-by="admin" default-license-id="this" suppress-on-update="true" suppress-if-required="true">
<license-text xlink:href="LICENSE" lang="en" license-id="this" />
</simple-license>
</registration>
<display-name>
<name lang="en">MRI - UNO Object Inspection Tool</name>
</display-name>
<icon>
<default xlink:href="icons/mri.png"/>
<high-contrast xlink:href="icons/mri_hc.png"/>
</icon>
<extension-description>
<src lang="en" xlink:href="descriptions/desc.en"/>
</extension-description>
<update-information>
<src xlink:href="https://github.com/hanya/MRI/raw/master/files/MRI.update.xml"/>
</update-information>
</description>"""

update_h = """<?xml version="1.0" encoding="UTF-8"?>
<description xmlns="http://openoffice.org/extensions/update/2006" 
xmlns:xlink="http://www.w3.org/1999/xlink"
xmlns:d="http://openoffice.org/extensions/description/2006">
<identifier value="mytools.mri" />
<version value="{VERSION}" />
<dependencies>
<d:OpenOffice.org-minimal-version value="3.4" d:name="OpenOffice.org 3.4" />
</dependencies>
<update-download>
<src xlink:href="https://github.com/hanya/MRI/releases/download/v{VERSION}/MRI-{VERSION}.oxt"/>
</update-download>
</description>"""

version = ""

def genereate_description(d):
    return desc_h.format(VERSION=version)

def generate_updatefeed(d):
    return update_h.format(VERSION=version)


def read_version():
    version = ""
    with open("VERSION") as f:
        version = f.read().strip()
    return version


def main():
    s = genereate_description({})
    with open("description.xml", "w") as f:
        f.write(s)
    s = generate_updatefeed({})
    with open("files/MRI.update.xml", "w") as f:
        f.write(s)


if __name__ == "__main__":
    version = read_version()
    main()
