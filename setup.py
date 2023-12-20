import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="raw-data-api",
    version="1.0.16",
    description="The Raw Data API  module makes it simple for you to get osm data stats provided by api in your own project",
    packages=setuptools.find_packages(),
    install_requires=[
        "pytest == 7.4.3",
        "psycopg2",
        "boto3==1.24.38",
        "fastapi==0.105.0",
        "geojson == 7.4.3",
        "area==1.1.1",
        "orjson==3.9.10",
        "slowapi==0.1.8",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Hot Tech Team",
    author_email="sysadmin@hotosm.org",
    url="https://github.com/hotosm/export-tool-api",
)
