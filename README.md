# moustic
<img src="doc/img/moustic.png" width="400" height="130" />

moustic is an interactive platform for exploring and analyzing movement in 3D.

Originally created for the ANOFEEL project - How ANOpheles Females sEEk maLes? (ANR-15-CE35-0001-01) - it was designed to analyze video-tracking data from malaria-vector mosquitoes during their swarming and mating phase, and to detect when mating pairs form.

Although conceived for mosquito research, moustic can handle any dataset that records the location of multiple objects in space and time - whether you are studying animal behavior, particle motion, swarm robotics etc.

The moustic application includes three modules:

	•	Mosqui'Track: Follow object trajectories in multiple formats, zoom in on selected paths, animate them over time, and measure distances between individuals frame by frame.
 
	•	Mosqui'Love: Identify and quantify interactions: who meets whom, when, and for how long, from approach to contact to separation.
 
	•	Mosqu'Investigate: Dive deeper with direction vectors, speed, and nearest-neighbor distances displayed in color gradients, perfect for spotting attraction, repulsion, and movement patterns.

Every module is packed with adjustable settings, giving you the freedom to explore your data your way. Whether for quick inspection or in-depth analysis, SwarmTrack turns raw coordinates into clear, dynamic visual stories.


<img src="doc/img/IRD.png" width="300" height="100" /> <img src="doc/img/MIVEGEC.png" width="150" height="100" />

---
For people unfamiliar with installing IT tools, help with installing and getting started with Moustic is available.

👉 **Access the documentation site here:** [moustic Web Page](https://anaisdenis.github.io/moustic/) 

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


## Installation of moustic

### Retrieve this file containing the codes and test 

[Download moustic as a ZIP file](https://github.com/AnaisDenis/moustic/archive/refs/heads/main.zip)

You can extract this folder to the directory of your choice: you will find the .zip file in your downloads. Move it by right-clicking, cutting, and pasting it into the directory of your choice. Then right-click and extract here.

### Install moustic

Once your virtual environment is activated and you are in the project directory (the folder that contains `pyproject.toml`), install moustic and its dependencies with:

    pip install .

This command will install:
- the `moustic` tool,
- all required dependencies

Now, if you copy and paste in your terminal : 
	
   python app.py

You should see a URL like this: http://127.0.0.1:8050/
You can click on it if it appears interactive. Otherwise, copy and paste this URL into your browser.

Congratulations ! You can use moustic !

Note: The Moustic app allows you to download swarm videos. This feature requires downloading an application (see Install FFMPEG section).
### Install FFMPEG

To download ffmpeg.exe, you can download the file in .7z [here]( https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.7z)
Or, you can download the file in .zip [here](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip)

Next, you need to unzip the downloaded file. Open the ffmpeg folder, then the bin folder. Copy the ffmpeg.exe file and paste it into the bin file located in the moustic-main folder.



## Project Structure
	
	│   .gitignore
	│   app.py
	│   CONTRIBUTING.md
	│   LICENSE
	│   mkdocs.yml
	│   pyproject.toml
	│   README.md
	│   requirements.txt
	│
	├───.github
	│   └───workflows
	│           main.yml
	│           mkdocs.yml
	│
	├───.idea
	│   │   .gitignore
	│   │   Detect_couple_v1.1.iml
	│   │   misc.xml
	│   │   modules.xml
	│   │   vcs.xml
	│   │
	│   └───inspectionProfiles
	│           profiles_settings.xml
	│           Project_Default.xml
	│
	├───assets
	│       moustic.png
	│
	├───data
	│       PostProc_Filtered_2020_09_03_18_15_53_Splined_reconstitue.csv
	│
	├───doc
	│   │   index.md
	│   │   install.md
	│   │   usage.md
	│   │
	│   └───img
	│           IRD.png
	│           MIVEGEC.png
	│
	└───src
	        callbacks.py
	        generate_video.py
	        layout.py
	        utils.py
	        __init__.py
	


## Contact

For questions or suggestions, please contact:
olivier.roux@ird.fr

Project developed by Anaïs DENIS as part of a Master's thesis on mosquito behavior analysis.
