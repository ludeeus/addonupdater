"""Setup configuration."""
import os
import time
import setuptools


for key in os.environ:
    print(key)

VERSION = str(time.time()).split('.')[0]

with open("README.md", "r") as fh:
    LONG = fh.read()
setuptools.setup(
    name="addonupdater",
    version=VERSION,
    author="Joakim Sorensen",
    author_email="ludeeus@gmail.com",
    description="",
    long_description=LONG,
    install_requires=['alpinepkgs', 'click', 'PyGithub>=1.43.4', 'requests'],
    long_description_content_type="text/markdown",
    url="https://github.com/ludeeus/addonupdater",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    entry_points={
        'console_scripts': [
            'addonupdater = addonupdater.cli:cli'
        ]
    }
)
