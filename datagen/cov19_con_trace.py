'''
Does Covid 19 contact tracing analysis on data of the form: 
<name, latitude, longitude, date, time, condition>
where name = name of the person, latitude & longitude are the geographical coordinates, date
& time are the time stamp when those coordinates were recorded and finally condition indicates
whether this person is sick or healthy.

Use generator.py to generate data in the above form with various configurations.

This program assumes that the input data is in the format prescribed above.

'''

import pandas as pd
import LatLon
from LatLon import *
import networkx as nx

##### All configurations start here #####

#data file path. this is the data to be analyzed.
datapath = '/mnt/c/Sushrut/Other projects/covid19/cont_trac_graph/githubrepo/Covid19/datagen/cov19_gen_dataset.csv'

##### All configurations end here   #####

##### Runtime variables #####
rawdataframe = pd.DataFrame()
persons = []

##### Methods #####

#customized printer
def printcov(str_to_print):
    print("[log]:--> " + str_to_print)

#Cleans and perpares data to be suitable for running analysis. Typically, this involves
#finding each unique person in the dataset, sorting the location records by time in an
#ascending order and others.
def dataprep():
    rawdataframe = pd.read_csv(datapath, sep=',', header=0)
    
    printcov("Sample of loaded raw data: ")
    print(rawdataframe.head(3))
    print(rawdataframe.tail(3))

    sorteddf = pd.DataFrame()
    popcount = 0
    lastname = ""

    #our goal is to get each unique name and then prepare data for that.
    for index, row in rawdataframe.iterrows():
        currname = row['name']
        if(currname != lastname):
            printcov("Processing for: " + currname)
            persons.append(currname)
            df = rawdataframe.loc[rawdataframe['name'] == currname]
            printcov("# of rows found: " + str(len(df)))
            popcount = popcount + 1

            #now to sort the rows by time. We ignore the Date field as we are assuming
            #that the data is of a single day only.
            df = df.sort_values(by=['time'])
            
            #finally append this to the sorted df
            sorteddf = sorteddf.append(df)
            lastname = currname

    printcov("Completed prep for data.")
    printcov("Sorted data: ")
    print(sorteddf.head(27))
    print(sorteddf.tail(27))
    printcov("Unique people found in pop of size: " + str(popcount))
    print(persons)
    printcov("Saving sorted data to a file: sorted_df.csv for debugging (in current folder).")
    sorteddf.to_csv("sorted_df.csv")

    return

#prepares graph data per unique person in the provided dataset and plots their travel
#history with locations and time. Also generates and adds useful attributes to nodes 
#and edges that help in further analysis. At this point, we know the total population
#size, the names of each unique person. We use this to plot a graph for analysis.
def graph_per_person():
    return

##### main #####
printcov("Starting Covid 19 contact tracing analysis for data in: ")
printcov(" " + datapath)

dataprep()

printcov("Completed Covid 19 contact tracing analysis.")
