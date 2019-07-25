"""Setup tools config."""
import setuptools

with open("README.md", "r") as fh:
    LONG = fh.read()

setuptools.setup(
    name="pydelijn",
    version="0.5.0",
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
        'aiohttp',
        'async_timeout',
        'pytz'
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
