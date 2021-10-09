import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="fit2gpx",                         # Package Name
    version="0.0.6",                        # Version - Initial release - README Updated
    author="Dorian Sabathier",              # Full name of the author
    author_email="dorian.sabathier+PyPi@gmail.com",
    url='https://github.com/dodo-saba/fit2gpx',
    license='GNU AGPLv3',                   # License

    description="Package to convert .FIT files to .GPX files, including tools for .FIT files downloaded from Strava",
    long_description=long_description,      # Long description read from the the readme file
    long_description_content_type="text/markdown",

    keywords=[
        'convert',
        '.fit', 'fit',
        '.gpx', 'gpx',
        'strava'
    ],

    install_requires=[
        'pandas',
        'gpxpy',
        'fitdecode'
    ],
    python_requires='>=3.6',                # Minimum version requirement of the package
    py_modules=["fit2gpx"],                 # Name of the python package
    package_dir={'': 'src'},        # Directory of the source code of the package


    classifiers=[                           # Information to filter the project on PyPi website
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Other Audience',
        'Topic :: Scientific/Engineering :: GIS',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10'
    ]
)
