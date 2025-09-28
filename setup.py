# setup.py (minimal)
from setuptools import setup, find_packages
setup(
    name="gdp-table-repo",
    version="0.1",
    packages=find_packages("src"),
    package_dir={"": "src"},
)
