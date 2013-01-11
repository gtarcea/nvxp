import os
from setuptools import setup
import nv


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="nvxp",
    version=nv.VERSION,
    author="V. Glenn Tarcea",
    author_email="glenn.tarcea@gmail.com",
    description="A cross-platform simplenote-syncing note-taking app inspired by Notational Velocity.",
    license="BSD",
    keywords="note-taking nvalt markdown multimarkdown",
    url="https://github.com/gtarcea/nvxp",
    packages=['nvxp'],
    long_description=read('README.rst'),
    install_requires=['Markdown', 'docutils'],
    entry_points={
        'gui_scripts': ['nv = nv:main']
    },
    # use MANIFEST.in file
    # because package_data is ignored during sdist
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: X11 Applications",
        "Environment :: MacOS X",
        "Environment :: Win32 (MS Windows)",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)
