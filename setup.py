#!/usr/bin/env python
from setuptools import setup, find_packages
import os

# Read the version from version.py without importing the package
version_file = os.path.join(os.path.dirname(__file__), 'src', 'enzywizard_interaction', 'version.py')
with open(version_file) as f:
    exec(f.read())  # defines __version__

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="enzywizard-interaction",
    version=__version__,                     # dynamically read from version.py (1.0.1)
    author="bioinfbrad",
    description=(
        "A command‑line tool for calculating protein/protein‑substrate molecular interactions "
        "and generating a detailed JSON report."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bioinfbrad/enzywizard-interaction",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.10",
    install_requires=[
        "biopython>=1.86",          # protein structure handling
        "rdkit>=2026.03.1",         # cheminformatics for substrates
        "numpy>=1.23.5",            # numerical backend
        "scipy>=1.15.2",            # KD‑tree acceleration
    ],
    entry_points={
        "console_scripts": [
            "enzywizard-interaction = enzywizard_interaction.cli:main",
        ],
    },
    include_package_data=True,
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Chemistry",
    ],
)
