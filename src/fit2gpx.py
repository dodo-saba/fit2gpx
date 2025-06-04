"""Classes to convert FIT files to GPX, including tools to process Strava Bulk Export
"""
import argparse
import gzip
import os
import shutil
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Union

import pandas as pd
from math import isnan
import lxml.etree as mod_etree

import fitdecode
import gpxpy.gpx


# MAIN CONVERTER CLASS
class Converter:
    """Main converter that holds the FIT > pd.DataFrame and pd.DataFrame > GPX methods"""

    def __init__(self, status_msg: bool = False):
        """Main constructor for StravaConverter
        Parameters:
            status_msg (bool): Option to have the Converter print to console with status messages,
            such as number of files converted.
        """
        self.status_msg = status_msg
        # The names of the columns will be used in our points and laps DataFrame
        # (use the same name as the field names in FIT file to facilate parsing)
        self._colnames_points = [
            'latitude',
            'longitude',
            'lap',
            'timestamp',
            'altitude',
            'enhanced_altitude',
            'temperature',
            'heart_rate',
            'cadence',
            'speed',
            'enhanced_speed',
            'power',
        ]

        self._colnames_laps = [
            'number',
            'start_time',
            'total_distance',
            'total_elapsed_time',
            'max_speed',
            'max_heart_rate',
            'avg_heart_rate'
        ]

        # Note: get_fit_laps(), get_fit_points(), get_dataframes() are shamelessly copied (and adapted) from:
        # https://github.com/bunburya/fitness_tracker_data_parsing/blob/main/parse_fit.py

    def _get_fit_laps(self, frame: fitdecode.records.FitDataMessage) \
            -> Dict[str, Union[float, datetime, timedelta, int]]:
        """Extract some data from a FIT frame representing a lap and return it as a dict.
        """
        # Step 0: Initialise data output
        data: Dict[str, Union[float, datetime, timedelta, int]] = {}

        # Step 1: Extract all other fields
        #  (excluding 'number' (lap number) because we don't get that from the data but rather count it ourselves)
        for field in self._colnames_laps[1:]:
            if frame.has_field(field):
                data[field] = frame.get_value(field)

        return data

    def _get_fit_points(self, frame: fitdecode.records.FitDataMessage) \
            -> Optional[Dict[str, Union[float, int, str, datetime]]]:
        """Extract some data from an FIT frame representing a track point and return it as a dict.
        """
        # Step 0: Initialise data output
        data: Dict[str, Union[float, int, str, datetime]] = {}

        # Step 1: Obtain frame lat and long and convert it from integer to degree (if frame has lat and long data)
        if not (frame.has_field('position_lat') and frame.has_field('position_long')):
            # Frame does not have any latitude or longitude data. Ignore these frames in order to keep things simple
            return None
        elif frame.get_value('position_lat') is None and frame.get_value('position_long') is None:
            # Frame lat or long is None. Ignore frame
            return None
        else:
            data['latitude'] = frame.get_value('position_lat') / ((2 ** 32) / 360)
            data['longitude'] = frame.get_value('position_long') / ((2 ** 32) / 360)

        # Step 2: Extract all other fields
        for field in self._colnames_points[3:]:
            if frame.has_field(field):
                data[field] = frame.get_value(field)

        return data

    def fit_to_dataframes(self, fname: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Takes the path to a FIT file and returns two Pandas DataFrames for lap data and point data
        Parameters:
            fname (str): string representing file path of the FIT file
        Returns:
            dfs (tuple): df containing data about the laps , df containing data about the individual points.
        """
        if isinstance(fname, str) or hasattr(fname, '__fspath__'):
            # Check that this is a .FIT file
            input_extension = os.path.splitext(fname)[1]
            if input_extension.lower() != '.fit':
                raise fitdecode.exceptions.FitHeaderError("Input file must be a .FIT file.")

        data_points = []
        data_laps = []
        lap_no = 1
        with fitdecode.FitReader(fname) as fit_file:
            for frame in fit_file:
                if isinstance(frame, fitdecode.records.FitDataMessage):
                    # Determine if frame is a data point or a lap:
                    if frame.name == 'record':
                        single_point_data = self._get_fit_points(frame)
                        if single_point_data is not None:
                            single_point_data['lap'] = lap_no  # record lap number
                            data_points.append(single_point_data)

                    elif frame.name == 'lap':
                        single_lap_data = self._get_fit_laps(frame)
                        single_lap_data['number'] = lap_no
                        data_laps.append(single_lap_data)
                        lap_no += 1  # increase lap counter

        # Create DataFrames from the data we have collected.
        # (If any information is missing from a lap or track point, it will show up as a "NaN" in the DataFrame.)

        df_laps = pd.DataFrame(data_laps, columns=self._colnames_laps)
        df_laps.set_index('number', inplace=True)
        df_points = pd.DataFrame(data_points, columns=self._colnames_points)

        return df_laps, df_points

    # Method adapted from: https://github.com/nidhaloff/gpx-converter/blob/master/gpx_converter/base.py
    def dataframe_to_gpx(self, df_points, col_lat='latitude', col_long='longitude', col_time=None, col_alt=None,
                         col_hr=None, col_cad=None, gpx_name=None, gpx_desc=None, gpx_link=None, gpx_type=None):
        """
        Convert a pandas dataframe to gpx
        Parameters:
            df_points (pd.DataFrame): pandas dataframe containing at minimum lat and long info of points
            col_alt (str): name of the altitudes column
            col_time (str): name of the time column
            col_long (str): name of the longitudes column
            col_lat (str): name of the latitudes column
            col_hr (str): name of the heart rate column
            col_cad (str): name of the cadence column
            gpx_name (str): name for the gpx track (note is not the same as the file name)
            gpx_desc (str): description for the gpx track
            gpx_type : activity type for the gpx track (can be str, or int)
            gpx_link (str): link to the gpx activity
        """
        # Step 0: Check that the input dataframe has all required columns
        cols_to_check = [col_lat, col_long]
        if col_alt:
            cols_to_check.append(col_alt)
        if col_time:
            cols_to_check.append(col_time)

        if any(elem not in df_points.columns for elem in cols_to_check):
            raise KeyError("The input dataframe must consist of point coordinates in longitude and latitude. "
                           "Ideally, it should be the df_points output from the fit_to_dataframes() method.")

        # Step 1: Initiate GPX object
        gpx = gpxpy.gpx.GPX()
        # -- create first track in our GPX:
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx.tracks.append(gpx_track)
        # -- create first segment in our GPX track:
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)

        # add extension to be able to add heartrate and cadence
        if col_hr or col_cad:
            gpx.nsmap = {'gpxtpx': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1'}
        
        # Step 2: Assign GPX track metadata
        gpx.tracks[0].name = gpx_name
        gpx.tracks[0].type = gpx_type
        gpx.tracks[0].description = gpx_desc if not pd.isna(gpx_desc) else None
        gpx.tracks[0].link = gpx_link

        # Step 3: Add points from dataframe to GPX track:
        for idx in df_points.index:
            # Create trackpoint:
            if isnan(df_points.loc[idx, col_alt]):
                track_point = gpxpy.gpx.GPXTrackPoint(
                    latitude=df_points.loc[idx, col_lat],
                    longitude=df_points.loc[idx, col_long],
                    time=pd.Timestamp(df_points.loc[idx, col_time]) if col_time else None,
                    # Do not include elevation if nan
                )
            else:
                track_point = gpxpy.gpx.GPXTrackPoint(
                    latitude=df_points.loc[idx, col_lat],
                    longitude=df_points.loc[idx, col_long],
                    time=pd.Timestamp(df_points.loc[idx, col_time]) if col_time else None,
                    elevation=df_points.loc[idx, col_alt] if col_alt else None,
                )

            # add GPX extensions for heartrate and cadence
            if col_hr or col_cad:
                namespace = '{gpxtpx}'
                root = mod_etree.Element(f'{namespace}TrackPointExtension')
                if col_hr:
                    sub_hr = mod_etree.SubElement(root, f'{namespace}hr')
                    sub_hr.text = str(df_points.loc[idx, col_hr]) if col_hr else '0'
                
                if col_cad:
                    sub_cad = mod_etree.SubElement(root, f'{namespace}cad')
                    sub_cad.text = str(df_points.loc[idx, col_cad]) if col_cad else '0'
                track_point.extensions.append(root)

            # Append GPX_TrackPoint to segment:
            gpx_segment.points.append(track_point)

        return gpx

    def fit_to_gpx(self, f_in, f_out):
        """Method to convert a FIT file into a GPX file
        Parameters:
            f_in (str): file path to FIT activity
            f_out (str): file path to save the converted FIT file
        """
        if isinstance(f_in, str) or hasattr(f_in, '__fspath__'):
            # Step 0: Validate inputs
            input_extension = os.path.splitext(f_in)[1]
            if input_extension != '.fit':
                raise Exception("Input file must be a .FIT file.")

        if isinstance(f_out, str) or hasattr(f_out, '__fspath__'):
            output_extension = os.path.splitext(f_out)[1]
            if output_extension != ".gpx":
                raise TypeError(f"Output file must be a .gpx file.")

        # Step 1: Convert FIT to pd.DataFrame
        df_laps, df_points = self.fit_to_dataframes(f_in)

        # Step 2: Fill gaps in data if FIT file recorded data only in enhanced altitude/speed columns:
        enhanced_fields = ['altitude', 'speed']
        for field in enhanced_fields:
            if df_points[field].count() == 0 and df_points[f'enhanced_{field}'].count() > 0:
                df_points[field] = df_points[field].fillna(df_points[f'enhanced_{field}'])

        # Step 3: Convert pd.DataFrame to GPX
        gpx = self.dataframe_to_gpx(
            df_points=df_points,
            col_lat='latitude',
            col_long='longitude',
            col_time='timestamp',
            col_alt='altitude',
            col_hr='heart_rate',
            col_cad='cadence',
        )

        # Step 3: Save file
        xml = gpx.to_xml()
        if hasattr(f_out, 'write'):
            f_out.write(xml)
        else:
            with open(f_out, 'w') as f:
                f.write(xml)

        return gpx

    def fit_to_gpx_bulk(self, dir_in, dir_out):
        """Method to convert all FIT files in a directory to GPX files
        Parameters:
            dir_in (str): path to directory with all FIT activities
            dir_out (str): path to directory to save the converted FIT files to
          """

        # Validate inputs (check that the input and output directories end with '/')
        if dir_in[-1] != '/':
            dir_in += '/'

        if dir_out and dir_out[-1] != '/':
            dir_out += '/'

        # -- check output directory exists, otherwise make dir
        if not os.path.isdir(dir_out):
            os.mkdir(dir_out)

        # Iterate through all files in indicated directory:
        # -- identify fit files
        fit_files = [f for f in os.listdir(dir_in) if '.fit' in f.lower()]

        for f_activity in fit_files:

            # Convert file and save to file
            self.fit_to_gpx(
                f_in=dir_in + f_activity,
                f_out=dir_out + os.path.splitext(f_activity)[0] + '.gpx'
            )

        # Print:
        if self.status_msg:
            print(f'{len(fit_files)} files converted from .fit to .gpx')


# STRAVA CONVERTER
class StravaConverter(Converter):
    """Converter to use when converting .FIT files from Strava data download to GPX files"""

    def __init__(self, dir_in, dir_out=None):
        """Main constructor for StravaConverter
        Parameters:
            dir_in (str): path to main strava data download folder
            dir_out (str): path to directory to save the converted FIT files to.
              If not provided, saves to an 'activities_gpx' directory in the main directory
        """
        super().__init__()
        # Check that the input and output directories end with '/':
        if dir_in[-1] != '/':
            dir_in += '/'

        if dir_out and dir_out[-1] != '/':
            dir_out += '/'

        # If no output directory provided, set to default:
        if not dir_out:
            dir_out = dir_in + 'activities_gpx/'

        # Check input directory has an activities folder and an activities.csv files
        if 'activities.csv' not in os.listdir(dir_in) or not os.path.isdir(dir_in + 'activities'):
            raise Exception('The input directory must be the main Strava data download directory, '
                            'i.e. must contain activities.csv and have a sub directory named "activities".')

        # -- check output directory exists, otherwise make dir
        if not os.path.isdir(dir_out):
            os.mkdir(dir_out)

        # If all checks out, assign directories to attributes:
        self._dir_in = dir_in
        self._dir_out = dir_out
        self._dir_activities = self._dir_in + 'activities/'

    def unzip_activities(self):
        """Method to unzip .gz files to their native format (e.g. gpx, tcx, fit, etc.)"""
        # Step 0: Count number of unique activity ids (sometimes an activity has both .fit and .fit.gz in the folder)
        cnt_activites = len({f.split('.')[0] for f in os.listdir(self._dir_activities)})

        # Step 1: Find zip files
        zip_paths = [self._dir_activities + f for f in os.listdir(self._dir_activities) if '.gz' in f]

        # 2. Unzip each file, and delete previous
        for path_zip in zip_paths:
            path_unzip = path_zip.replace('.gz', '')

            # Check if file has already been unzipped:
            if path_unzip in os.listdir(self._dir_activities):
                continue

            else:
                # Unzip file
                with gzip.open(path_zip, 'rb') as f_in:
                    with open(path_unzip, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                # Delete zip file
                os.remove(path_zip)

        # Step 3: Check the correct number of activities is given
        if self.status_msg:
            if len(os.listdir(self._dir_activities)) == cnt_activites:
                print(f'{len(zip_paths)} zipped files have been unzipped')
            else:
                print('ERROR: Certain files have been deleted. Oopsies.')

    def strava_fit_to_gpx(self):
        """Method to convert all FIT files in a directory to GPX files, adding metadata from Strava to GPX files
        """

        # Step 2: Read the activities metadata:
        df_acts = pd.read_csv(self._dir_in + '/activities.csv').fillna('')

        # Step 3: Iterate through all files in indicated directory:

        fit_files = [f for f in os.listdir(self._dir_activities) if '.fit' in f.lower()]

        for f_activity in fit_files:

            # Step 3.1: Convert FIT to pd.DataFrame
            df_laps, df_points = self.fit_to_dataframes(self._dir_activities + f_activity)

            # Step 3.2: Identify FIT file metadata from Strava log
            # -- identify corresponding activity in md
            md = df_acts.loc[df_acts['Filename'].str.contains(f_activity)].iloc[0, :].to_dict()
            act_id = md['Activity ID']
            act_name = md['Activity Name']
            act_desc = md['Activity Description']

            # -- check on values
            if not act_name.isascii():
                act_name = str(act_name.encode('ascii', 'ignore'))  # drop emojis

            if pd.isna(act_desc):
                act_desc = None
            elif not act_desc.isascii():  # drop emojis
                act_desc = str(act_desc.encode('ascii', 'ignore'))

            # -- assign desired metadata
            strava_args = {
                'gpx_name': act_name,
                'gpx_type': md['Activity Type'],
                'gpx_desc': act_desc,
                'gpx_link': f"https://www.strava.com/activities/{act_id}"
            }

            # Step 3.3: Convert pd.DataFrame to GPX
            gpx = self.dataframe_to_gpx(
                df_points=df_points,
                col_lat='latitude',
                col_long='longitude',
                col_time='timestamp',
                col_alt='altitude',
                col_hr='heart_rate',
                col_cad='cadence',
                **strava_args
            )

            # Step 3.4: Save gpx
            path_out = self._dir_out + f'{act_id}.gpx'
            with open(path_out, 'w') as f:
                f.write(gpx.to_xml())

            # Step 3.5: Print
            if self.status_msg:
                print(f'{len(fit_files)} files have been converted from .fit to .gpx files containing Strava metadata')

    def add_metadata_to_gpx(self):
        """Method adds Strava metadata to default GPX files (i.e. files downloaded as GPX from Strava)"""

        # Step 0: Identify GPX files from 'activities' folder,
        # skipping those which have already had metadata added to them and been moved to the output dir:
        gpx_files = [f for f in os.listdir(self._dir_activities) if '.gpx' in f and f not in os.listdir(self._dir_out)]

        # Step 1: Read the activities metadata:
        df_acts = pd.read_csv(self._dir_in + '/activities.csv').fillna('')

        # Step 2: Iterate through gpx files
        for gpx_path in gpx_files:
            # Step 2.1: Identify GPX file metadata from Strava log
            # -- identify corresponding activity in md
            md = df_acts.loc[df_acts['Filename'].str.contains(gpx_path)].iloc[0, :].to_dict()
            act_id = md['Activity ID']
            act_name = md['Activity Name']
            act_desc = md['Activity Description']

            # -- check on values
            if not act_name.isascii():
                act_name = str(act_name.encode('ascii', 'ignore'))  # drop emojis

            if pd.isna(act_desc):
                act_desc = None
            elif not act_desc.isascii():  # drop emojis
                act_desc = str(act_desc.encode('ascii', 'ignore'))

            # Step 2.2: Add metadata to GPX file
            # -- open GPX file
            f_gpx = open(self._dir_activities + gpx_path, 'r', encoding='utf-8')
            gpx = gpxpy.parse(f_gpx)

            # Skip any file that does not have tracks (i.e. no geospatial data, e.g. workouts or pool swims)
            if len(gpx.tracks) == 0:
               continue

            # -- assign GPX track metadata
            gpx.tracks[0].name = act_name
            gpx.tracks[0].type = md['Activity Type']
            gpx.tracks[0].description = act_desc
            gpx.tracks[0].link = f"https://www.strava.com/activities/{act_id}"

            # Step 2.3: Save gpx
            path_out = self._dir_out + f'{act_id}.gpx'
            with open(path_out, 'w') as f:
                f.write(gpx.to_xml())

            # Step 2.4: Print
            if self.status_msg:
                print(f'{len(gpx_files)} .gpx files have had Strava metadata added.')


def cli():
    parser = argparse.ArgumentParser(
        prog='fit2gpx',
        description="Convert a .FIT file to .GPX."
    )
    parser.add_argument(
        'infile',
        type=argparse.FileType('rb'),
        help='path to the input .FIT file; '
        "use '-' to read the file from standard input"
    )
    parser.add_argument(
        'outfile',
        type=argparse.FileType('wt'),
        help='path to the output .GPX file; '
        "use '-' to write the file to standard output"
    )
    args = parser.parse_args()

    conv = Converter()
    conv.fit_to_gpx(f_in=args.infile, f_out=args.outfile)
