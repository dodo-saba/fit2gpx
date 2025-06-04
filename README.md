[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) [![Documentation Status](https://readthedocs.org/projects/fit2gpx/badge/?version=latest)](https://fit2gpx.readthedocs.io/en/latest/?badge=latest) [![GitHub license](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

<a href="https://www.buymeacoffee.com/doriansaba" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/guidelines/download-assets-sm-3.svg" alt="Buy Me A Coffee" style="height: 60px" ></a>


# fit2gpx -- convert .fit to .gpx
This is a simple Python library for converting .FIT files to .GPX files. It also includes tools to convert Strava data downloads in bulk to GPX.
- [FIT](https://developer.garmin.com/fit/overview/) is a GIS data file format used by Garmin GPS sport devices and Garmin software
- [GPX](https://docs.fileformat.com/gis/gpx/) is an XML based format for GPS tracks.

# When: Use Cases
1. You need to convert .FIT files to pandas dataframe (e.g. for data analysis)
2. You need to convert .FIT files to .GPX
3. You need to fix files downloaded from Strava by converting the raw .FIT files to their .GPX counterparts

# Why
#### Motivation
I decided to create this package after spending a few hours searching for a simple solution to quickly convert hundreds of FIT files to GPX. I needed to do this as GIS applications do not parse FIT files. Whilst a few solutions existed, they are command line scripts which offered very little flexibility.

#### Relevance to Strava
- Pre-GPDR, you could bulk export all your Strava activities as GPX files.
- Post-GDPR, you can export an archive of your account. Whilst this includes much more data, activity GPS files are now downloaded in their original file format (eg. GPX or FIT format, some gzipped, some not) and named like 2500155647.gpx, 2500155647.gpx.gz, 2500155647.fit,  and 2500155647.fit.gz.
- [How to bulk export you Strava Data](https://support.strava.com/hc/en-us/articles/216918437-Exporting-your-Data-and-Bulk-Export#Bulk)

# Overview
The fit2gpx module provides two converter classes:
- Converter: used to convert a single or multiple FIT files to pandas dataframes or GPX files
- StravaConverter: used to fix all the Strava Bulk Export problems in three steps:
    1. Unzip GPX and FIT files
    2. Add activity metadata to existing GPX files
    3. Convert FIT files to GPX including activity metadata from Strava)

# Use Case 1: FIT to pd.DataFrame
Step 1: Import module and create converter object
```python
from fit2gpx import Converter

conv = Converter()
```
Step 2: Convert FIT file to 2 pd.DataFrame: fit_to_dataframes()
```python
df_lap, df_point = conv.fit_to_dataframes(fname='3323369944.fit')
```
- df_laps: information per lap: lap number, start time, total distance, total elapsed time, max speed, max heart rate, average heart rate
- df_points: information per track point: longitude, latitude, altitude, timestamp, heart rate, cadence, speed, power, temperature
  - Note the 'enhanced_speed' and 'enhanced_altitude' are also extracted. Where overlap exists with their default counterparts, values are identical. However, the default or enhanced speed/altitude fields may be empty  depending on the device used to record ([detailed information](https://pkg.go.dev/github.com/tormoder/fit#RecordMsg)).


# Use Case 2: FIT to GPX
Import module and create converter object
```python
from fit2gpx import Converter

conv = Converter()          # create standard converter object
```
Use case 2.1: convert a single FIT file: fit_to_gpx()
```python
gpx = conv.fit_to_gpx(f_in='3323369944.fit', f_out='3323369944.gpx')
```

Use case 2.2: convert many FIT files to GPX files: fit_to_gpx_bulk()
```python
conv.fit_to_gpx_bulk(dir_in='./project/activities/', dir_out='./project/activities_convert/')
```

# Use Case 3: Strava Bulk Export Tools (FIT to GPX conversion)
Copy the below code, adjusting the input directory (DIR_STRAVA), to fix the Strava Bulk Export problems discussed in the [overview](#Overview).
```python
from fit2gpx import StravaConverter

DIR_STRAVA = 'C:/Users/dorian-saba/Documents/Strava/'

# Step 1: Create StravaConverter object
# - Note: the dir_in must be the path to the central unzipped Strava bulk export folder
# - Note: You can specify the dir_out if you wish. By default it is set to 'activities_gpx', which will be created in main Strava folder specified.

strava_conv = StravaConverter(
    dir_in=DIR_STRAVA
)

# Step 2: Unzip the zipped files
strava_conv.unzip_activities()

# Step 3: Add metadata to existing GPX files
strava_conv.add_metadata_to_gpx()

# Step 4: Convert FIT to GPX
strava_conv.strava_fit_to_gpx()
```

# Command line interface

You can install this package using pip:

```shell
pip install --user --upgrade .
```

And then you can run the `fit2gpx` command to convert a FIT file to GPX:

```shell
fit2gpx 3323369944.fit 3323369944.gpx
```

You can also read the FIT file from standard input and/or write the GPX file to
standard output:

```shell
fit2gpx - 3323369944.gpx < 3323369944.fit
fit2gpx 3323369944.fit - > 3323369944.gpx
```

To see the help, run:

```shell
fit2gpx -h
```

# Dependencies
#### pandas
[pandas](https://github.com/pandas-dev/pandas) is a Python package that provides fast, flexible, and expressive data structures designed to make working with "relational" or "labeled" data both easy and intuitive.
#### gpxpy
[gpxpy](https://github.com/tkrajina/gpxpy) is a simple Python library for parsing and manipulating GPX files. It can parse and generate GPX 1.0 and 1.1 files. The generated file will always be a valid XML document, but it may not be (strictly speaking) a valid GPX document.
#### fitdecode
[fitdecode](https://github.com/polyvertex/fitdecode) is a rewrite of the [fitparse](https://github.com/dtcooper/python-fitparse) module allowing to parse ANT/GARMIN FIT files.


