# Lovely Rita

# Shapefiles: https://github.com/openoakland/lovely-rita/wiki/Data-Sources

# To do
# - Finding the neighborhood/council district for tickets is very slow. Try to speed that up.
# - Rewrite the JS to load the data as more proper JSON objects. See See https://codepen.io/KryptoniteDove/post/load-json-file-locally-using-pure-javascript
# - When clicking on a region in the map, display a more detailed report about the region, perhaps using D3.
# - Install cenpy and try to get Oakland census data with it. See https://earthdatascience.org/tutorials/get-cenus-data-with-cenpy/
# - Perform some basic inquiries (e.g. do some neighborhoods have higher average tickets for the same violation, and what are their demographic characteristics?)
# - How to go from lat/long to block face?
# - Consider https://geopy.readthedocs.io/en/1.10.0/

# Instructions
# - This code assumes that lovely-rita-clean.csv file has already been created from the Lovely Rita code. If not, go here: https://github.com/openoakland/lovely-rita/wiki/Data-Sources
# - You also need the shapefiles for Oakland neighborhoods and city council districts. Get them here: https://github.com/openoakland/lovely-rita/wiki/Data-Sources
# - Unzip the shapefiles in the previous step and put those directors in the data directory
# - This file should be at the root of the project directory. lovely-rita-clean.csv should be in the data directory.
# - Change the os.chdir(...) line to the proper project directory
# - If you are running this for the first time, first run the full script to initialize data and functions. Then run run_full(). Be warned that it will take a while.
# - If you already have the latlon.csv file, use rerun() instead.

import pandas as pd
import numpy as np
import os
import json # For exporting data for Javascript Code
import shapefile
from shapely.geometry import shape, Point, Polygon
from pyproj import Proj, transform

# Fill in your project directory here
os.chdir("/Users/michaelgoff/Desktop/Machine Learning/lovely-rita-mods")
# Read in the output of the python notebooks that clean the data. This might take a couple minutes.
df = pd.read_csv("data/lovely-rita-clean.csv")

# Because of the long time it takes to process the shape files, we will track progress
num_done = 0
# Find out which neighborhood(s) a point is in. Return a list, possibly empty
def get_shape(lon,lat,polygons):
    results = [i for i in range(len(polygons)) if polygons[i].contains(Point(lon,lat))]
    global num_done
    num_done += 1
    if num_done % 1000 == 0:
        print str(num_done) + " / " + str(len(df)) + " completed."
    # For our purposes we want to insure that there is exactly one result return, perhaps -1 if no neighborhood
    if len(results) == 0:
        return -1
    return results[0]

def load_shapes(filename,colname):
    global num_done
    num_done = 0
    map_shapes = shapefile.Reader(filename)
    # The buffer(0) is because some shapes are evidently flawed
    if colname == "council":
        # Converting coordinates for these shapefiles. See OaklandCityCouncilDistricts.prj
        inProj = Proj(init='esri:102643', preserve_units=True) # Source for this projection: http://www.spatialreference.org/ref/?page=2&search=calif
        outProj = Proj(init='epsg:4326')
        polygons = [Polygon([transform(inProj,outProj,p[0],p[1]) for p in map_shapes.shapes()[i].points]) for i in range(len(map_shapes.shapes()))]
    else:
        polygons = [Polygon(map_shapes.shapes()[i].points) for i in range(len(map_shapes.shapes()))]
    df[colname] = df.apply(lambda row: get_shape(row["Longitude"],row["Latitude"],polygons),axis=1)
    
# Create JS objects storing polygon coordinates for easy use with HTML
def shape_to_JSON(filename,outfile,projection = ""):
    map_shapes = shapefile.Reader(filename)
    points = []
    if len(projection) > 0:
        inProj = Proj(init=projection, preserve_units=True)
        outProj = Proj(init='epsg:4326')
        points = [[transform(inProj,outProj,p[0],p[1]) for p in map_shapes.shapes()[i].points] for i in range(len(map_shapes.shapes()))]
    else:
        points = [[[p[0],p[1]] for p in map_shapes.shapes()[i].points] for i in range(len(map_shapes.shapes()))]
    json_file = open("data/"+outfile+".js", "w")
    json_file.write(outfile + " = " + json.dumps(points))
    json_file.close()
    json_file = open("data/"+outfile+"_records.js", "w")
    json_file.write(outfile + "_records = " + json.dumps(map_shapes.records()))
    json_file.close()
    
# Save all the shapefiles to usable JSON objects
def shapes_to_JSON():
    shape_to_JSON("data/ceda_neighborhoods2002/ceda_neighborhoods2002.shp","neighborhood_shapes")
    shape_to_JSON("data/OaklandCityCouncilDistricts/OaklandCityCouncilDistricts.shp","council_shapes","esri:102643")

# Get the regions for all points in the system.
# Warning: this can be quite slow. On my machine, loading the neighborhoods shapefiles takes over an hour.
def determine_shapes():
    load_shapes("data/ceda_neighborhoods2002/ceda_neighborhoods2002.shp","neighborhood")
    load_shapes("data/OaklandCityCouncilDistricts/OaklandCityCouncilDistricts.shp","council")
    # Save the new columns to a separate CSV file so we won't have to calculate them every time.
    # For later runs, load the latlon file and transfer the relevant columns to df
    df_latlon = df[["Latitude","Longitude","neighborhood","council"]]
    df_latlon.to_csv("data/latlon.csv")
    
def dollar_to_num(amt):
    if isinstance(amt,basestring):
        return float(amt.split('$')[1])
    return 0
    
def date_to_year(date):
    if isinstance(date,basestring):
        return date[-2:]
    return "?"
    
# This function create aggregates that are saved as JS files for use in the web app
# Aggregate properties (e.g. number of tickets or average fine)
def aggregates():
    # Convert fine amounts from string to numerical values (dollars)
    df["Fine Amount Num"] = df.apply(lambda row: dollar_to_num(row["Fine Amount"]),axis=1)
    df["Year"] = df.apply(lambda row: date_to_year(row["Ticket Issue Date"]),axis=1)
    df_by_year = {}
    years = ["12","13","14","15","16"]
    for y in years:
        df_by_year[y] = df[df["Year"]==y]
        
    # Number of tickets by neighborhood
    df_agg = df.groupby(["neighborhood"]).size().reset_index(name="counts")
    df_agg_by_year = {}
    for y in years:
        df_agg_by_year[y] = df_by_year[y].groupby(["neighborhood"]).size().reset_index(name="counts")
    agg_object = {df_agg.ix[i][0]:{"count":df_agg.ix[i][1]} for i in range(len(df_agg))}
    for y in years:
        for i in range(len(df_agg_by_year[y])):
            agg_object[df_agg_by_year[y].ix[i][0]][y] = df_agg_by_year[y].ix[i][1]
    json_file = open("data/neighborhood_count.js", "w")
    json_file.write("nc = " + json.dumps(agg_object))
    json_file.close()
    
    # Number of tickets by council district
    df_agg = df.groupby(["council"]).size().reset_index(name="counts")
    df_agg_by_year = {}
    for y in years:
        df_agg_by_year[y] = df_by_year[y].groupby(["council"]).size().reset_index(name="counts")
    agg_object = {df_agg.ix[i][0]:{"count":df_agg.ix[i][1]} for i in range(len(df_agg))}
    for y in years:
        for i in range(len(df_agg_by_year[y])):
            agg_object[df_agg_by_year[y].ix[i][0]][y] = df_agg_by_year[y].ix[i][1]
    json_file = open("data/council_count.js", "w")
    json_file.write("cc = " + json.dumps(agg_object))
    json_file.close()
    
    # Dollar value sum of tickets by neighborhood
    df_sum = df.groupby(["neighborhood"]).sum()
    agg_object = [{"neighborhood":i,"fines":df_sum["Fine Amount Num"][i]} for i in df_sum.index]
    json_file = open("data/neighborhood_fines.js", "w")
    json_file.write("nf = " + json.dumps(agg_object))
    json_file.close()
    
    # Dollar value sum of tickets by council district
    df_sum = df.groupby(["council"]).sum()
    agg_object = [{"council":i,"fines":df_sum["Fine Amount Num"][i]} for i in df_sum.index]
    json_file = open("data/council_fines.js", "w")
    json_file.write("cf = " + json.dumps(agg_object))
    json_file.close()
    
    # Share of tickets by type in 2016
    ticket_types = np.unique(df_by_year["16"]["Violation Description Long"])
    df16 = df_by_year["16"]
    df_agg = df16.groupby(["neighborhood"]).size().reset_index(name="counts")
    for t in ticket_types:
        df_ticket = df16[df16["Violation Description Long"]==t]
        df_ticket_agg = df_ticket.groupby(["neighborhood"]).size().reset_index(name=t)
        df_agg = df_agg.merge(df_ticket_agg, left_on='neighborhood', right_on='neighborhood', how='left')
        df_agg[t] = df_agg[t] / df_agg["counts"]
    df_agg = df_agg.fillna(0)
    agg_object = [{"neighborhood":df_agg["neighborhood"][i],"tickets": {t:df_agg[t][i] for t in ticket_types} }for i in df_agg.index]
    json_file = open("data/ticket_types.js", "w")
    json_file.write("ticket_types = " + json.dumps(agg_object))
    json_file.close()

def run_full():
    determine_shapes()
    shapes_to_JSON()
    aggregates()
    
def rerun():
    df_latlon = pd.read_csv("data/latlon.csv")
    df["neighborhood"] = df_latlon["neighborhood"]
    df["council"] = df_latlon["council"]
    shapes_to_JSON()
    aggregates()