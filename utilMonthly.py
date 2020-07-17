import json
import traceback
import os
from os import listdir
from os.path import isfile, join
import copy

oldData = {}

def save_data(year,month,obj, name ):
	global oldData
	
	if (not isinstance(obj, (list,)) and (not isinstance(obj, str))):
		if not os.path.exists('save/'+str(year)+"/"+str(month)+"/"+ name):
			os.makedirs('save/'+str(year)+"/"+str(month)+"/"+ name)
		
		if not year in oldData:
			oldData[year] = {}
		if not month in oldData[year]:
			oldData[year][month] = {}
		
		if not name in oldData[year][month]:
			oldData[year][month][name] = {}
		
		for id in obj:
			needsSave = False
			if not id in oldData[year][month][name]:
				#print("id "+str(id)+" does not exist in save")
				needsSave = True
			else:
				if oldData[year][month][name][id] != obj[id]:
					#print("id "+str(id)+" has changed")
					needsSave = True
				#else:
					#print(oldData[name][id],obj[id])
			
			if needsSave:
				try:
					with open('save/'+str(year)+"/"+str(month)+"/"+ name +"/"+str(id)+ '.json', 'w') as f:
						#print("Save data start")
						json.dump(obj[id], f)
						#print("Save data finish")
				except Exception as ex:
					print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
			#else:
				#print("id "+str(id)+" has not changed")
		
		for oldId in oldData[year][month][name]:
			validToRemove = True
			if str(oldId) in obj:
				validToRemove = False
			try:
				if int(oldId) in obj:
					validToRemove = False
			except:
				pass
			
			if validToRemove:
				try:
					os.remove('save/'+str(year)+"/"+str(month)+"/"+ name +"/"+str(oldId)+ '.json')
				except:
					print("Error when removing unsued id from "+str(name)+" ID "+str(oldId))
			
		oldData[year][month][name] = copy.deepcopy(obj)
		
	elif isinstance(obj, str):
		#print("Going to save string")
		try:
			if not name in oldData[year][month]:
				oldData[year][month][name] = ""
			oldData[year][month][name] = copy.deepcopy(obj)
			with open('save/'+ name + '.json', 'w') as f:
				#print("Save data start")
				json.dump(obj, f)
				#print("Save data finish")
		except Exception as ex:
			print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
			
	else:
		try:
			if not name in oldData[year][month]:
				oldData[year][month][name] = {}
			oldData[year][month][name] = copy.deepcopy(obj)
			with open('save/'+ name + '.json', 'w') as f:
				#print("Save data start")
				json.dump(obj, f)
				#print("Save data finish")
		except Exception as ex:
			print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))

def load_data(year,month,name):
	global oldData
	
	if not year in oldData:
		oldData[year] = {}
	if not month in oldData[year]:
		oldData[year][month] = {}
		
	oldData[year][month][name] = {}
	#print("Trying to load folder",str(name))
	
	try:
		onlyfiles = [f for f in listdir('save/'+str(year)+"/"+str(month)+"/"+ name+"/") if isfile(join('save/'+str(year)+"/"+str(month)+"/"+ name+"/", f))]
	except:
		#print("Error reading folder "+str(name))
		onlyfiles = []
		
	for file in onlyfiles:
		#print(str(file))
		id = str(file).replace(".json","")
		if os.path.isfile('save/'+str(year)+"/"+str(month)+"/"+ name +"/"+str(file)):
			try:
				with open('save/'+str(year)+"/"+str(month)+"/"+ name +"/"+str(file), 'r') as f:
					oldData[year][month][name][id] = json.load(f)
			except Exception as ex:
				print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
	
	return copy.deepcopy(oldData[year][month][name])
		
def load_data1File(name):
	global oldData
	
	oldData[name] = []
	
	if os.path.isfile('save/' + name + '.json'):
		try:
			with open('save/' + name + '.json', 'r') as f:
				oldData[name] = json.load(f)
				return copy.deepcopy(oldData[name])
		except Exception as ex:
			print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
	else:
		oldData[name] = []
		return []