import pandas as pd
import LatLon
from LatLon import *

##### All configurations start here #####

#data file path. this is the data to be analyzed.
datapath = '/mnt/c/Sushrut/Other projects/covid19/cont_trac_graph/githubrepo/Covid19/datagen/cov19_con_trace.py'

##### All configurations end here   #####


#Cleans and perpares data to be suitable for running analysis. Typically, this involves
#finding each unique person in the dataset, sorting the location records by time in an
#ascending order and others.
def dataprep():
    return

#prepares graph data per unique person in the provided dataset and plots their travel
#history with locations and time. Also generates and adds useful attributes to nodes 
#and edges that help in further analysis.
def graph_per_person():
    return

##### main #####
print("Starting Covid 19 contact tracing analysis for data in: ")
print("")

print("Completed Covid 19 contact tracing analysis.")