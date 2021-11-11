"""Setup tools config."""
import re

import setuptools

with open("README.md", "r") as fh:
    LONG = fh.read()

with open("pydelijn/__init__.py", "r") as fd:
    version = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE
    ).group(1)

setuptools.setup(
    name="pydelijn",
    version=version,
    author="bollewolle",
    author_email="dev@bollewolle.be",
    python_requires=">=3.5.0",
    description=("Get realtime info on stop passages "
                 "of De Lijn (api.delijn.be)"),
    long_description=LONG,
    long_description_content_type="text/markdown",
    url="https://github.com/bollewolle/pydelijn",
    packages=setuptools.find_packages(exclude=('tests',)),
    install_requires=[
        'aiohttp>=3.6.2,<4.0',
        'async_timeout>=4.0.0,<5.0',
        'pytz>=2020.1'
    ],
    license='MIT',
    classifiers=(
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
    ),
)
