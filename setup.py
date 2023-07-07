# Copyright (C) 2023, NG:ITL
import versioneer
from pathlib import Path
from setuptools import find_packages, setup


def read(fname):
    return open(Path(__file__).parent / fname).read()


setup(
    name="raai_module_template",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author="NGITl",
    author_email="p.altmann@hotmail.de",
    description=("RAAI Module for sending Commands to the Platform"),
    license="GPL 3.0",
    keywords="template",
    url="https://github.com/vw-wob-it-edu-ngitl/raai_module_template",
    packages=find_packages(),
    long_description=read("README.md"),
    install_requires=["pynng~=0.7.2"],
)
