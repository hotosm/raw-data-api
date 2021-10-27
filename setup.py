import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='osm_stats',
    version='0.0.1',
    description=
    'The osm_stats module makes it simple for you to get osm data stats provided by api in your own project',
    packages=["osm_stats"],
    extras_require={
        "dev": [
            "pytest == 3.7",
            "psycopg2",
            "testing.postgresql==1.3.0",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    python_requires='>=3',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Hot Tech Team",
    author_email="sysadmin@hotosm.org",
    url="https://github.com/hotosm/osm-stats-api")
