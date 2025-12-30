import numpy as np
import pandas as pd
import pathlib
import logging
import trackpy as track
import argparse

# Configure the logging level and format
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

parser = argparse.ArgumentParser(description="Convert track CSV into GPX file.")
parser.add_argument("--input", "-i", help="CSV file to read.")
parser.add_argument("--output", "-o", help="GPX file to write.")
parser.add_argument("--fit", help="Optional .fit file to include heart rate data.")
parser.add_argument(
    "--sessions", "-s", help="Which sessions to include. Omit to include all sessions."
)

args = parser.parse_args()

csvfile = pathlib.Path(args.input)
gpxfile = pathlib.Path(args.output)
if args.sessions is None:
    sessions = None
else:
    sessions = list(map(int, args.sessions.split(",")))


# Construct Velodrome
velodrome_csv = pathlib.Path("eddy_merckx_wielercentrum_wgs84.csv")
name = ("Eddy Merckx Wielercentrum",)
elevation = 7
start_finish = np.round(np.pi * 27.7 + 2 * 38, decimals=1)

# construct Velodrome from scratch
if not velodrome_csv.is_file():
    wielercentrum = track.velodrome.Velodrome(
        name,
        center_utm=(548540.34, 5655259.58),
        rotation=-18,
        length=250,
        precision=0.1,
        elevation=elevation,
        start_finish=start_finish,
    )
    wielercentrum.save(velodrome_csv)

# construct from csv if it exists
else:
    arc_length_wgs84 = pd.read_csv(velodrome_csv)

    wielercentrum = track.velodrome.BaseVelodrome(
        name,
        elevation=elevation,
        start_finish=start_finish,
        arc_length_wgs84=arc_length_wgs84,
    )

filename = pathlib.Path(csvfile)
parsing_info = f"Parsing {filename}"
if sessions:
    parsing_info += f" for sessions {sessions}"
else:
    parsing_info += f" for all sessions"

# Parse transponder
logging.info(parsing_info)
transponder = track.parse_transponder(filename, sessions=sessions)

# Combine transponder and velodrome
logging.info(f"Mapping {filename} to the Eddy Merck wielercentrum")
interpolation = track.map_interpolation_to_velodrome(transponder, wielercentrum)

fit = None
if args.fit:
    fit_path = pathlib.Path(args.fit)
    tz = interpolation["Interpolated time (s)"].dt.tz
    tz_name = tz.zone if hasattr(tz, "zone") else str(tz)
    fit = track.read_fit(fit_path, tz=tz_name)
    has_hr = "heartrate" in fit and fit["heartrate"].notna().any()
    if has_hr:
        logging.info("Including heart rate data from FIT file.")
    else:
        logging.info("FIT file loaded but no heart rate data found.")
else:
    logging.info("No FIT file provided; GPX will not include heart rate data.")

# Write to GPX
logging.info(f"Writing to {gpxfile}")
track.write_gpx(gpxfile, interpolation, fit=fit, velodrome=wielercentrum)
