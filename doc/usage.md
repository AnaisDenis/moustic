# General of moustic

## Description of the app moustic 

The application offers several advanced and interactive visualization features for mosquito swarms. Once the application is open, you can directly select a csv data file. This file must have the structure detailed in the "Requirements" section.
This application is composed of three parts:
- MosquiTrack for swarm visualization
- Mosquit'Love for pair detection
- Mosqu'Investigate for research on stereotypical behaviors before mating

## Exigence 

To use this code, you need a CSV file in the following format:

- **object**: an integer identifier representing an object tracked over time.

- **time**: a decimal number representing the elapsed time in seconds.

- **XSplined**: the object's position along the X-axis (horizontal coordinate), expressed as a decimal number.

- **YSplined**: the object's position along the Y-axis (vertical coordinate), expressed as a decimal number.

- **ZSplined**: the object's position along the Z-axis (depth or height), expressed as a decimal number.

- **VXSplined**: the object's velocity along the X-axis, expressed as a decimal number.

- **VYSplined**: the object's velocity along the Y-axis, expressed as a decimal number.

- **VZSplined**: the object's velocity along the Z-axis, expressed as a decimal number.

Each row of the file therefore corresponds to the state of an object at a given moment, including its spatial position and velocity in all three dimensions.

Example (excerpt):

| object 	| time 		| XSplined 	| YSplined 	| ZSplined 	| VXSplined 	| VYSplined 	| VZSplined 	|
|---------------|---------------|---------------|---------------|---------------|---------------|---------------|---------------|
| 1	 	| 3.151  	| 0.192		| -0.152	|-0.111		| 0.465 	| -0.050	| 0.403		|
| 1 	 	| 3.171		| 0.201		| -0153		| -0.103	| 0.470		|-0.044		| 0.396	 	|


## select a csv data file

<img src="/moustic/img/mosquitrack/charger_fichier.png" />

Once you have selected the csv file in your local files, information about the structure of your file will appear. You can see its name, the number of objects/mosquitoes with a trajectory, and the time range entered in your csv files.
