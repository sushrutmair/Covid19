"""
This program generates data of the form: <name, latitude, longitude, date, time, condition>
where name = name of the person, latitude & longitude are the geographical coordinates, date
& time are the time stamp when those coordinates were recorded and finally condition indicates
whether this person is sick or healthy.

The default logic values set 5% of the population as sick with Covid19. 50% of the population
is set to 'linger' which means that they roam in a regimented geographical area around their
start coordinates. This is to account for activities like visiting a food truck, market area or
a sports arena. The other 50% are set to be 'passthru' which means that they roam randomly in
the overall geographical area. This is to account for people who are just passing through or
do not spend too much time in a single small geo area.

Dependencies:
 - Python 2.7 only (one library doesn't support Python 3 :(.)
 - latlon library - pip install latlon
 - pandas
"""

import random
import decimal
import string
import datetime
import pandas as pd
import LatLon
from LatLon import *

#configurations used to generate the data
total_readings = 24
total_pop = 10
sick_percent = 5 #% of total pop that is sick
no_of_sick_allowed = ((total_pop*sick_percent)/100)
name_size = 7
timehr_range_start = 17
timehr_range_end = 21
timemm_range_start = 10
timemm_range_end = 60
#the four below restrict the generation of arbitrary location coordinates
#to a certain geographical area. It is a roughly rectangular block carved
#from a locality.
latstart = 18565000
latend = 18565500
lonstart = 73907100
lonend = 73910999

col_names = ['name','lat','lon','date','time','condition']
datasetdf = pd.DataFrame(columns = col_names)

if(no_of_sick_allowed<1):
	no_of_sick_allowed = 1

print("Starting generation of data ...")
print("Max sick allowed: " + str(no_of_sick_allowed) + " out of total population: " + str(total_pop))
curr_sick = 0
mark_sick = 0
glinger = False

def generate_dyndata(linger):

	if(linger):#regimented locations against contracted timeframes
		print("linger")
		regimented_datagen()
	else:#random locations against random timeframes
		print("passthru")
		random_datagen()

def regimented_datagen():

	return

def random_datagen():

	return

#main
for p in range(0, total_pop):
	name = ''.join(random.choice(string.ascii_uppercase) for _ in range(name_size))
	#print(name)
	condition = "healthy"
	if(mark_sick==0):
		con = random.randint(10,20)
		if(con>=15):
			condition = "sick"
			curr_sick = curr_sick + 1
			if(curr_sick>=no_of_sick_allowed):
				mark_sick = 1

	#print("Person: " + name + " is: " + condition)
	if(glinger):
		glinger = False
	else:
		glinger = True

	generate_dyndata(glinger)
	
	for p2 in range(0, total_readings):
		x = datetime.datetime.now()
		date = x.strftime("%d-%m-%Y")
		#print(date)
	
		timehr = random.randint(timehr_range_start, timehr_range_end)
		timemm = random.randint(timemm_range_start, timemm_range_end)
		time = str(timehr) + str(timemm)
		#print(time)

		lat=decimal.Decimal(random.randrange(latstart,latend))/1000000
		lon=decimal.Decimal(random.randrange(lonstart,lonend))/1000000
		currloc = LatLon(Latitude(lat),Longitude(lon))
		#print(currloc) #the current location of this person

		datasetdf = datasetdf.append({'name': name, 'lat':lat, 'lon':lon, 'date': date, 'time': time, 'condition': condition}, ignore_index=True)

	print("Generated data points for: " + str(p) + " people.")

print("Completed generation...now writing to CSV file...")
datasetdf.to_csv("cov19_gen_dataset.csv")
print("Wrote file.")
#print(datasetdf)
