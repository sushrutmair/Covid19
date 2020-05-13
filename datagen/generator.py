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
do not spend too much time in a single small geo location.

Dependencies:
 - Python 2.7 only (latlon doesn't support Python 3 :(.)
 - latlon library - https://pypi.org/project/LatLon/
 - pandas
"""

import random
import decimal
import string
import datetime
import pandas as pd
import LatLon
from LatLon import *

##### all configurables end here #####

#configurations used to generate the data

#no of loc readings to be taken in configured time range
total_readings = 24

#total no of people for whom readings are to be generated
total_pop = 5

#% of total pop that is sick
sick_percent = 5

#actual no of people allowed to be sick within the entire population
no_of_sick_allowed = ((total_pop*sick_percent)/100)

#length of the name of the person
name_size = 7

#the below configurations control the times when the readings start
#to the time readings stop. this is the configured time range
timehr_range_start = 17
timehr_range_end = 21
timemm_range_start = 10
timemm_range_end = 60

#the four below restrict the generation of arbitrary location coordinates
#to a certain geographical area. It is a roughly rectangular block carved
#from a locality. You can put your own but be careful to establish that
#the location start and end are close by to indicate proper contact
latstart = 18565000
latend = 18565500
lonstart = 73907100
lonend = 73910999

#num of start locations for regimented movements of people. People who have
#regimented movements (linger), move around these areas only
total_linger_start_loc = 5
#linger_mov_angle = 135
#this decides the heading (bearing) a person will move to. Note that the
#actual bearing is a product of this param + total_linger_start_loc's
#current value. If total_linger_start_loc goes over 24, there could be
#runtime issues
linger_mov_angle_mulfactor = 15

##### all configurables end here #####

#dataframe that holds all regiemented (linger) start locations
col_regloc = ['lat','lon']
reglocdf = pd.DataFrame(columns = col_regloc)

#the main dataframe that holds all generated data in memory
col_names = ['name','lat','lon','date','time','condition']
datasetdf = pd.DataFrame(columns = col_names)

#for sanity
if(no_of_sick_allowed<1):
	no_of_sick_allowed = 1

#some dynamic runtime configs
curr_sick = 0
mark_sick = 0
glinger = False
reglocindex = 0

#decides to call generations for linger or passthru
def generate_dyndata(linger, name, condition,locindx):

	if(linger):#regimented locations against contracted timeframes
		print("linger")
		return regimented_datagen(name,condition,locindx)
	else:#random locations against random timeframes
		print("passthru")
		return random_datagen(name, condition)

#data gen for lingering population. Specific start loc and then
#linger around that loc every few min till iterations complete. The
#start time is random but then intervals are regulated till all
#linger iterations are completed.
def regimented_datagen(name, condition,locindx):

	dfregi = pd.DataFrame(columns = col_names)

	x = datetime.datetime.now()
	date = x.strftime("%d-%m-%Y")

	timehr = random.randint(timehr_range_start, timehr_range_end)
	timemm = random.randint(timemm_range_start, timemm_range_end)
	time = str(timehr) + str(timemm)

	#the start loc is drawn from the reglocdf
	basestartloc = LatLon(Latitude(reglocdf['lat'].values[locindx]),Longitude(reglocdf['lon'].values[locindx]))

	dfregi = dfregi.append({'name': name, 
		'lat':reglocdf['lat'].values[locindx], 
		'lon':reglocdf['lon'].values[locindx], 
		'date': date, 'time': time, 'condition': condition}, ignore_index=True)

	timehr1 = timehr
	timemm1 = timemm
	day = x.strftime("%d")
	mon = x.strftime("%m")
	yr  = x.strftime("%Y")
	loc = basestartloc
	for p2 in range(0, total_readings-1):
		#generate and apply a path iteratively against time. thus we get lat,lon and time here. the rest have
		#been filled from either func parameters or generated just before this.
		mnte = int(timemm1)
		if(mnte>59):
			mnte = 59
		y = datetime.datetime(year = int(yr), month=int(mon), day=int(day), hour=int(timehr1), minute=mnte)
		z = y + datetime.timedelta(0,59)

		#generate a next loc for this timestamp z starting from basestartloc
		nextloc = loc.offset(locindx*linger_mov_angle_mulfactor,0.002)
		lat1 = nextloc.to_string()[0]
		lon1 = nextloc.to_string()[1]


		#reset the variables to increment properly next loop
		timehr1 = z.strftime("%H")
		timemm1 = z.strftime("%M")
		loc = nextloc

		#append the dataframe for this person for each iteration so that we store a linger path over a period of time
		#first ensure that the right time hr and min variables are used as well as lat, lon
		time1 = str(timehr1) + str(timemm1)
		dfregi = dfregi.append({'name': name, 'lat':lat1, 'lon':lon1, 'date': date, 'time': time1, 'condition': condition}, ignore_index=True)

	return dfregi

#gen regimented start locations. Used as a base to generate regimented
#linger paths for some part of the population.
def gen_reg_start_loc(total_start_pos):

	if(total_start_pos>24):
		total_start_pos = 24

	reglocdf1 = pd.DataFrame(columns = col_regloc)

	for num in range(0, total_start_pos):
		lat=decimal.Decimal(random.randrange(latstart,latend))/1000000
		lon=decimal.Decimal(random.randrange(lonstart,lonend))/1000000
		reglocdf1 = reglocdf1.append({'lat': Latitude(lat),'lon': Longitude(lon)},ignore_index=True)

	return reglocdf1

#data gen for passthru population
def random_datagen(name, condition):

	dfrandom = pd.DataFrame(columns = col_names)

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

		dfrandom = dfrandom.append({'name': name, 'lat':lat, 'lon':lon, 'date': date, 'time': time, 'condition': condition}, ignore_index=True)

	#print(dfrandom)
	return dfrandom

#main
print("Starting generation of data ...")
print("Max sick allowed: " + str(no_of_sick_allowed) + " out of total population: " + str(total_pop))
reglocdf = gen_reg_start_loc(total_linger_start_loc)
print("Regimented start locations are: ")
print(reglocdf)

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

	datasetdf = datasetdf.append(generate_dyndata(glinger,name,condition,reglocindex))
	reglocindex = reglocindex + 1
	if(reglocindex>=total_linger_start_loc):
		reglocindex = 0

	print("Generated data points for: " + str(p+1) + " people.")

print("Completed generation...now writing to CSV file...")
datasetdf.to_csv("cov19_gen_dataset.csv")
print("Wrote file. Generator will exit now.")
#print(datasetdf)
