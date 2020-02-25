"""Setup tools config."""
import setuptools

with open("README.md", "r") as fh:
    LONG = fh.read()

setuptools.setup(
    name="pystibmvib",
    version="0.0.6",
    author="helldog136",
    author_email="dev.helldog136@outlook.com",
    python_requires=">=3.5.0",
    description=("Get realtime info on stop passages "
                 "of STIB/MVIB (opendata-api.stib-mivb.be)"),
    long_description=LONG,
    long_description_content_type="text/markdown",
    url="https://github.com/helldog136/pystibmvib",
    download_url="https://github.com/helldog136/pystibmvib/archive/0.0.6.tar.gz",
    packages=setuptools.find_packages(exclude=('tests',)),
    install_requires=[
        'async_timeout',
        'aiohttp',
        'pytz',
        'asyncio',
        'pyshp'
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
