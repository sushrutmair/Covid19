'''
Does Covid 19 contact tracing analysis on data of the form: 
<name, latitude, longitude, date, time, condition>
where name = name of the person, latitude & longitude are the geographical coordinates, date
& time are the time stamp when those coordinates were recorded and finally condition indicates
whether this person is sick or healthy.

Use generator.py to generate data in the above form with various configurations.

This program assumes that the input data is in the format prescribed above. It takes this data
and then builds various directed as well as undirected graphs. It use the graphs to:
 - detect potential high risk contacts
 - detect risky locations
 - detect vulnerable subset of the population
 - predict potential future vulnerable population / locations

Dependencies:
- Python 2.7 only (latlon doesn't support Python 3 :(. For python 3+, use pyGeodesy)
- LatLon 1.0.2 - https://pypi.org/project/LatLon/
- pandas 0.24.2
- networkx 2.2 ( !pip install networkx=2.2. 2.2 due to python 2.7 - use latest if on Python 3+ )
- python-louvain 0.13 ( !pip install python-louvain )
- matplotlib 2.2.4

'''

import pandas as pd
import LatLon
from LatLon import *
import networkx as nx
import matplotlib.pyplot as plt
import time
from copy import deepcopy
import community

##### All configurations start here #####

#set for lat, lon otherwise implicit default loses precision
pd.set_option('display.precision',12)

#data file path. this is the data to be analyzed.
datapath = 'cov19_gen_dataset_05 _doctored.csv' #'cov19_gen_dataset_10k.csv'

#stores the size of the virtual microcell around each location a person was recorded to have visited.
#this is used to calculate if two persons have breached the commonly accepted social distance limits.
#can be changed to anything, default is kept at x metres. This is for tagging high risk contacts.
microcell_radius = 0.01 # default is 0.003. It is about 10 ft captured here in metres

#controls whether graphs are visually displayed or not. If running on linux ensure X Windows is available.
#0 = graphs are displayed in ui. 1 = no graphs are displayed.
ui = 1

##### All configurations end here   #####

##### Runtime variables #####
rawdataframe = pd.DataFrame()
sorteddf = pd.DataFrame() #same as raw data frame except all locations are sorted asc order by time of visit
persons = []
all_locs_unnormalized = [] #holds all recorded locations in an array
gxarry_pop_travel_hist = [] #array of nx graphs holding travel history of each member in pop
undir_gxarray_pop_travel_hist = []#same graph as gxarry_pop_travel_hist except it is undirected
col_breach = ['name1','con1','latlon1','entrytm1','exittm1','name2','con2','latlon2',
    'entrytm2','exittm2','dist','breach', 'risk']

#holds info of all possible travels by the population and which two people were involved. This
#is used to generate a risk profile for the population.
travel_hist = pd.DataFrame(columns = col_breach)

#graph with various new edges and attributes on both nodes and edges. Used for
#overall analysis activities.
biggx = nx.Graph()

#list of known infected people
infected_list = []

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

    popcount = 0
    lastname = ""
    dftmp = pd.DataFrame()

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
            dftmp = dftmp.append(df)
            lastname = currname

    printcov("Completed prep for data.")
    #sorteddf = sorteddf.append(dftmp)
    dftmp = dftmp.reset_index(drop=True)
    printcov("Prepp'd data: ")
    print(dftmp.head(27))
    print(dftmp.tail(27))
    printcov("Unique people found in pop of size: " + str(popcount))
    print(persons)
    printcov("Saving prepp'd data to a file: preppd_df.csv for debugging (in current folder).")
    dftmp.to_csv("preppd_df.csv")

    return dftmp

#prepares graph data per unique person in the provided dataset and plots their travel
#history with locations and time. Also generates and adds useful attributes to nodes 
#and edges that help in further analysis. At this point, we know the total population
#size, the names of each unique person. We use this to plot a graph for analysis.
def graph_per_person(person):
    printcov("Generating graph for: " + person)
    one_persons_records = sorteddf.loc[sorteddf['name'] == person] #sorted by time in asc order
    one_persons_records = one_persons_records.reset_index(drop=True)
    print(one_persons_records)
    gx = nx.MultiDiGraph(name=person,con=one_persons_records['condition'][0]) #new graph for curr person

    #create all nodes
    nodeid=0
    for index, row in one_persons_records.iterrows():
        #each recorded loc is a node
        nodelabel = str(person) + str(nodeid)
        gx.add_node(nodelabel,latlon=LatLon(Latitude(row['lat']),Longitude(row['lon'])))
        nodeid = nodeid+1
    
    noofnodes = nx.number_of_nodes(gx)

    #now let's add edges for the nodes
    print("Adding edges for: " + str(nx.number_of_nodes(gx)) + " nodes...")
    print(gx.nodes())
    for x in range(0,noofnodes):
        y = x + 1
        if(y == noofnodes):
            print("reached end node")
            break
        else:
            nodelabel1 = str(person) + str(x)
            nodelabel2 = str(person) + str(y)
            #gx.add_edge(nodelabel1,nodelabel2,time=one_persons_records.at[nodelabel2,'time'])
            gx.add_edge(nodelabel1,nodelabel2,time=one_persons_records['time'][y])

    print("Completed adding edges for: " + str(person) + ". Graph complete.")

    disp_graph(gx)
    gxarry_pop_travel_hist.append(gx)

    return

#finds overlapping locations with time for the population and also marks such
#locations with a new attribute so that we can easily analyze them later. We also
#create a new undirected graph that has all overlaps available. There shall be one
#such overlap graph per person in the population.
def overlaps_for_pop(gxall):
    printcov("Finding overlaps within population's location history")
    b_all = pd.DataFrame(columns = col_breach)
    for x in range(0, len(gxall)):
        #get the 1st person and find overlaps of each of their loc
        #with each loc of each other person in the population.
        
        #we convert the graph to an undirected copy since mixed graphs are
        #not possible in nx. We'll use both versions for later analysis. Note
        #that the loc overlap calc doesnt need undirected graph. We shall create
        #a new undirected edge for each overlap and that is why we need to
        #convert to undirected graph
        undirectedgxcurr = gxall[x].to_undirected() #get this person's graph
        
        #compare current person graph with all others for loc overlaps
        #first copy out the graph container
        gxallminuscurr = []
        for cv in range(0,len(gxall)):
            newgx = deepcopy(gxall[cv]) #use a deep copy
            gxallminuscurr.append(newgx)

        gxallminuscurr.pop(x)#remove current persons graph before cmp
        for y in range(0, len(gxallminuscurr)):
            undirectedgxnext = gxallminuscurr[y].to_undirected()
            disp_graph(undirectedgxnext)
            bxy = find_overlap(undirectedgxcurr,undirectedgxnext)
            b_all = b_all.append(bxy)
            
    printcov("Completed overlap extractions.")
    return b_all

#finds overlapping locations between two graphs
def find_overlap(undgx_curr, undgx_next):
    #get 'latlon' attributes of both and figure out if present in microcell
    anchorgraph_name = str(undgx_curr.graph['name'])
    compargraph_name = str(undgx_next.graph['name'])
    anchor_health_status = str(undgx_curr.graph['con'])
    compar_health_status = str(undgx_next.graph['con'])
    printcov("Processing overlaps. Anchor graph: " + anchorgraph_name + " | " + 
        anchor_health_status + " and Comparison graph: " 
        + compargraph_name + " | " + compar_health_status)
    gxcurr_nodeattrib = nx.get_node_attributes(undgx_curr,'latlon')
    gxnext_nodeattrib = nx.get_node_attributes(undgx_next,'latlon')
    printcov("Node attributes for overlap calc are:\n")
    print("curr anchor graph: " + str(gxcurr_nodeattrib))
    print("comparison  graph: " + str(gxnext_nodeattrib))
    print("\n")

    b = pd.DataFrame(columns = col_breach)

    for x in range(0, len(gxcurr_nodeattrib)):
        for y in range(0, len(gxnext_nodeattrib)):
            #here, we compare curr(latlon) with next(latlon) iteratively.
            gxcurr_curr_nodelbl = str(anchorgraph_name) + str(x)
            gxnext_curr_nodelbl = str(compargraph_name) + str(y)
            print(str(gxcurr_nodeattrib[gxcurr_curr_nodelbl]) + " ----- " + str(gxnext_nodeattrib[gxnext_curr_nodelbl]))
            distance = gxcurr_nodeattrib[gxcurr_curr_nodelbl].distance(gxnext_nodeattrib[gxnext_curr_nodelbl])
            print("Person: " + anchorgraph_name +  " & Person " + compargraph_name)
            print("     - anchor node: " + str(gxcurr_curr_nodelbl) + "  and comparison node: " + str(gxnext_curr_nodelbl))
            print("     - distance between above two: " + str(distance))

            entm1 = find_startime_gx(x, undgx_curr, anchorgraph_name)
            extm1 = find_endtime_gx(x, undgx_curr, anchorgraph_name)

            entm2 = find_startime_gx(y, undgx_next, compargraph_name)
            extm2 = find_endtime_gx(y, undgx_next, compargraph_name)
            
            risk = 'none'
            breach = 'no'
            if(distance <= microcell_radius):
                
                #a new edge connecting these two nodes and save the graph. Also mark
                #the relevant loc's as 'breached' with a new node attribute. risk is still
                #classified as none because we have not yet calculated time overlap
                print("Microcell radius breached.")
                breach = 'yes'
                #breachnodes attribute is useful to find edges that caused a breach
                biggx.add_edge(gxcurr_curr_nodelbl,gxnext_curr_nodelbl,
                    breachnodes=(gxcurr_curr_nodelbl+':'+gxnext_curr_nodelbl))
                biggx.nodes[gxcurr_curr_nodelbl]['breached'] = 'yes'
                biggx.nodes[gxnext_curr_nodelbl]['breached'] = 'yes'

                #time overlaps. use e*tm1 and e*tm2 to calculate overlap. If there is
                #an overlap of time then we have two people in the same location at the same
                #time => risk == high if one of them is sick. For the h person mark the loc as
                #infection start time (potentially). We already have the time at that place tho
                #the actual start time should be the time h and s were together first at this loc.
                #risk = 'high'
                if(max(entm1,entm2) <= min(extm1,extm2)):
                    print("Time overlap found too. Checking if one of them is sick..")
                    if( (anchor_health_status=='sick') or (compar_health_status=='sick')):
                        print("One person is sick. Marked as high risk for healthy.")
                        risk = 'high'
                        if(anchor_health_status=='healthy'):
                          biggx.nodes[gxcurr_curr_nodelbl]['infec_start_loc'] = 'yes'
                        if(compar_health_status=='healthy'):
                          biggx.nodes[gxnext_curr_nodelbl]['infec_start_loc'] = 'yes'
            
            data = pd.DataFrame([[anchorgraph_name, anchor_health_status, 
                    gxcurr_nodeattrib[gxcurr_curr_nodelbl], entm1, extm1, 
                    compargraph_name, compar_health_status,
                    gxnext_nodeattrib[gxnext_curr_nodelbl], entm2, extm2, 
                    distance, breach, risk]],
                    columns=['name1','con1','latlon1','entrytm1','exittm1','name2','con2',
                        'latlon2','entrytm2','exittm2','dist','breach', 'risk'])
            b = b.append(data)

    return b

#finds the exit time for the given graph's node. exit time = time when the person exited a recorded loc
def find_endtime_gx(nodelabelsuffix, gx, nodelabelprefix):
    curr_node = str(nodelabelprefix) + str(nodelabelsuffix)
    prev_node_sfx = 0
    next_node_sfx = 0
    if(nodelabelsuffix == 0):
        prev_node_sfx = 0
    else:
        prev_node_sfx = nodelabelsuffix-1

    if(nodelabelsuffix ==len(gx)-1):
        next_node_sfx = nodelabelsuffix
    else:
        next_node_sfx = nodelabelsuffix + 1

    extm1 = 0
    next_node = str(nodelabelprefix) + str(next_node_sfx)
    if(gx.has_edge(curr_node,next_node)):
        extm1 = gx.get_edge_data(curr_node,next_node)
        extm1 = extm1[0]['time']
    
    return extm1

#finds the start time for the given graph's node. start time = time when a person entered a recorded loc
def find_startime_gx(nodelabelsuffix, gx, nodelabelprefix):
    curr_node = str(nodelabelprefix) + str(nodelabelsuffix)
    prev_node_sfx = 0
    next_node_sfx = 0
    if(nodelabelsuffix == 0):
        prev_node_sfx = 0
    else:
        prev_node_sfx = nodelabelsuffix-1

    if(nodelabelsuffix ==len(gx)-1):
        next_node_sfx = nodelabelsuffix
    else:
        next_node_sfx = nodelabelsuffix + 1

    entm1 = 0
    prev_node = str(nodelabelprefix) + str(prev_node_sfx)
    if(gx.has_edge(prev_node,curr_node)):
        entm1 = gx.get_edge_data(prev_node,curr_node)
        entm1 = entm1[0]['time']
    
    return entm1

#allows to validate all graphs. For each graph, walks it, explodes nodes and edges.
def test_all_graphs(g):
    printcov("=========> Testing all graphs: ")
    for i in range(0, len(g)):
        print(nx.info(g[i]))

        print(" - Nodes:")
        print(g[i].nodes)
        for x1 in range(0, len(g[i].nodes)):
            nodelabel = str(g[i].graph['name']) + str(x1)
            print("Node id: " + str(nodelabel) + str(g[i].nodes[nodelabel]))
            #print("Node id: " + str(x1) + str(g[i].nodes[x1]))
        
        print(" - Edges:")
        print(g[i].edges)
        print("Edge attributes: " + str(nx.get_edge_attributes(g[i],'time')))
        
        print('------------------------------------------')
    printcov("=========> Testing complete.")
    return

#builds a graph for all of the population. Is an undirected
#graph and is used for running analysis algorithms.
def build_bigdaddy(gxarray):

    gxdaddytemp = nx.MultiGraph()
    for i in range(0,len(gxarray)):
        gxdaddytemp = nx.compose(gxdaddytemp,gxarray[i].to_undirected())

    return gxdaddytemp

#display graphs
def disp_graph(g):
    if(ui == 0):
        nx.draw(g, with_labels=True)
        nx.draw_networkx_edge_labels(g, pos=nx.spring_layout(g))
        plt.show()

def save_graph_to_pickle(g, filename):
    nx.write_gpickle(g, filename)
    return

def read_graph_from_pickle(picklepath):
    g = nx.read_gpickle(picklepath)
    return g

def find_infection_start_locs(g):
    nattrib_infec_start_loc = nx.get_node_attributes(g,'infec_start_loc')
    printcov("Infection start locations for healthy people are: \n" + str(nattrib_infec_start_loc))
    return nattrib_infec_start_loc

def find_high_traffic_locations(g):
    node_deg = dict(nx.degree(g))
    sorted_nodedeg = [(k, node_deg[k]) for k in sorted(node_deg, key=node_deg.get, reverse=True)]
    top5nodes_by_deg = []
    top5nodes_by_deg.append(sorted_nodedeg[0])
    top5nodes_by_deg.append(sorted_nodedeg[1])
    top5nodes_by_deg.append(sorted_nodedeg[2])
    top5nodes_by_deg.append(sorted_nodedeg[3])
    top5nodes_by_deg.append(sorted_nodedeg[4])

    di = nx.get_node_attributes(g,'breached')

    printcov("These locations have witnessed high traffic: ")
    htl = []
    for n in g.nodes:
        for n2 in top5nodes_by_deg:
            if(n == n2[0]):
                for n3 in di:
                    if(n2[0] == n3):
                        print(str(n3))
                        htl.append(n3)
    return htl

def predict_next_infec_locations(g):
    neighb_nodes=[]

    infec_start_locs = nx.get_node_attributes(g,'infec_start_loc')
    for n in infec_start_locs:
        neighb = nx.all_neighbors(g,n)
        for nebs in neighb:
            neighb_nodes.append(nebs)

    #we can also order these location edges by time by keeping locs that come into play
    #only after the 'infec_start_loc' time. This keeps predicted locs that were traveled
    #to only after an infection occured. The below is a more generic set.
    printcov("Predicted locations where infections may have occurred (time agnostic): ")
    print(neighb_nodes)

    return neighb_nodes

#note: this function plots a graph if ui is enabled
def find_communities_based_on_loc(g):

    #first compute the best partition
    G = g
    partition = community.best_partition(G)

    comm_list = []    
    size = float(len(set(partition.values())))
    count = 0.
    for com in set(partition.values()) :
        count = count + 1.
        list_nodes = [nodes for nodes in partition.keys()
                                    if partition[nodes] == com]
        comm_list.append(list_nodes)

    if(ui == 0):
        plt.figure(101,(17,17))
        pos = nx.spring_layout(G)
        nclr = range(len(list_nodes))
        nx.draw_networkx_nodes(G, pos, list_nodes, node_size = 150, node_color = nclr)
        #print("node color: ",nclr, ". For community: ", list_nodes, "\n")
        nx.draw_networkx_edges(G, pos, alpha=0.5)
        plt.show()

    printcov("Final list of ", len(comm_list), " louvain modularized communities :=>\n")
    for x in comm_list:
        print(x)
    
    return comm_list

def find_vuln_loc_and_ppl(comm_list, infperson):

    vulncomm = [] #list of vulnerable locations
    for comm in comm_list:
        for p in comm:
            onlyname = ''.join([i for i in p if not i.isdigit()])
            if(onlyname == infperson):
                vulncomm.append(comm)
                break
    printcov("Priority list of vulnerable locations are: ")
    print(vulncomm)
    
    vulnppl1 = []
    for x in vulncomm:
        for j in range(0,len(x)):
            onlyname = ''.join([i for i in x[j] if not i.isdigit()])
            vulnppl1.append(onlyname)

    printcov("Vulnerable people are: ")
    vulnppl = list(set(vulnppl1))
    print(vulnppl)

    return vulncomm, vulnppl

def find_known_infected_ppl(g):
    return infected_list

def run_graph_analysis(g):
    
    infperson_lst = find_known_infected_ppl(g)
    
    find_infection_start_locs(g)
    
    find_high_traffic_locations(g)
    
    predict_next_infec_locations(g)
    
    comm_list = find_communities_based_on_loc(g)

    for infp in infperson_lst:
        onlyname = ''.join([i for i in infp if not i.isdigit()])
        find_vuln_loc_and_ppl(comm_list, onlyname)

    return

################
##### MAIN #####
################
printcov("Starting Covid 19 contact tracing analysis for data in: ")
printcov(" " + datapath)
printcov("Configurations are: ")
print("Microcell radius for overlap calc: " + str(microcell_radius))
print("Graph display control is: " + str(ui) + ".   0 = ON / 1 = OFF.")
print('-------------------------------------')
time.sleep(7.7)

#call dataprep method. We also get 'persons' during this
sorteddf = dataprep()

infected_list = (sorteddf.loc[sorteddf['condition'] == 'sick'])['name'].unique()
printcov("We have: " + str(len(infected_list)) + " known infected people in this dataset. They are: ")
print(infected_list)

#call graph generation method for each person in the dataset
print("Initiating graph generation...")
for person in range(0,len(persons)):
    graph_per_person(persons[person])

test_all_graphs(gxarry_pop_travel_hist)

biggx = build_bigdaddy(gxarry_pop_travel_hist)

travel_hist = overlaps_for_pop(gxarry_pop_travel_hist)
printcov("There are : " + str(len(travel_hist)) + " travel histories. They are: ")
print(travel_hist)
#save travel hist for later use
travel_hist.to_csv("travelhist_df.csv")
disp_graph(biggx)

save_graph_to_pickle(biggx, "graph.gz")

run_graph_analysis(biggx)

printcov("Completed Covid 19 contact tracing analysis.")
