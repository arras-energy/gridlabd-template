import gridlabd
def on_init(t):
	# ATTACH THE POLES TO LINE OBJECTS BASED ON LAT / LONG
	model_objects = gridlabd.get("objects")
	pole_objects = []
	pole_coordinates = {}
	for model_object in model_objects : 
		if "pole" == gridlabd.get_value(model_object, "class") or "powerflow.pole" == gridlabd.get_value(model_object, "class"):
			pole_objects.append(model_object)
			pole_coordinates[model_object]={"latitude" : gridlabd.get_value(model_object, "latitude"), "longitude" : gridlabd.get_value(model_object, "latitude") }
	print(pole_coordinates)
	# for pole in pole_objects : 
	# gridlabd.get_value("")
	# print(pole_objects)

	return True