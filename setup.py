import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="export-tool-api",
    version="0.0.1",
    description="The export tool api module makes it simple for you to get osm data stats provided by api in your own project",
    packages=["src"],
    package_dir={"export_tool_api": "src"},
    extras_require={
        "dev": [
            "pytest == 3.7",
            "psycopg2",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Hot Tech Team",
    author_email="sysadmin@hotosm.org",
    url="https://github.com/hotosm/export-tool-api",
)
