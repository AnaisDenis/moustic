# Detect_couple

 	  cd path_name

    python -m venv env

    .\env\Scripts\activate

    pip install .

    python app.py



This project allows us to visualize swarms of mosquitoes, detect interactions from their trajectories and provides access to some research ideas on the nature of these interactions.

<img src="doc/img/IRD.png" width="300" height="100" /> <img src="doc/img/MIVEGEC.png" width="150" height="100" />

---

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

### Open a terminal
A terminal (or command prompt) is a tool that allows you to interact with your computer by typing text commands. Unlike a graphical interface (where you click buttons), the terminal allows you to execute specific instructions, such as launching a Python script, installing libraries, or navigating through your project folders.

**Windows**: Press Windows + R, type cmd, and then press Enter.

**macOS**: Open the Terminal application via Spotlight (Cmd + Space, then type "Terminal").

**Linux**: Use the shortcut Ctrl + Alt + T or search for "Terminal" in your applications menu.

To install Pmosquito, you need Python 

### Check if Python is Installed

Type the following command:

	python --version

or 

	python3 --version

If you see something like Python 3.x.x, Python is already installed. Otherwise, proceed to the next step.

### Install Python

**For Windows**

Go to https://www.python.org/downloads/windows/

Click Download Python 3.x.x

IMPORTANT: On the first installation screen, check the box "Add Python to PATH"

Click Install Now

After installation, reopen your terminal and check:

	python --version

**For macOS**

If needed, install Homebrew

Use the following command:

	brew install python


**For Linux (Debian, Ubuntu, etc.)**

Use the following commands:

	sudo apt update
	sudo apt install python3 python3-venv python3-pip

### Install pip (if not already installed)

Most modern Python installations include pip. To check:

	pip --version

or

	pip3 --version

If it's missing:

On Windows, reinstall Python and ensure "Install pip" is checked

On Linux, use:

	sudo apt install python3-pip

### Virtual Environment

It is recommended to use a virtual environment:

- Each virtual environment contains its own version of Python and its own packages, independent of other projects or the system installation. This prevents a package update for one project from breaking another.
- You can install exactly the versions of libraries needed for one project without affecting others. Perfect for replicating an environment on another machine.

In your terminal you need to move to the Pmosquito-main directory
You must write in your terminal: 
	
 	cd path_name

**Note**: To find your path:
Open File Explorer.
Go to your project folder.
Click in the address bar at the top: the path will appear.

Then, type :

	python -m venv env

Here, env is the name of the virtual environment. You can choose a different name if you wish.
This creates an env/ folder containing an isolated Python installation.

Then ypu need to activate your virtual environment. Type always in your terminal :

**For Windows**

	.\env\Scripts\activate

**For Linux/macOS**

	source env/bin/activate

Normally you should see your virtual environment name displayed in parentheses at the beginning of the new command line

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


## Tests files


## Available Parameters


## Run Example


## Contact

For questions or suggestions, please contact:
olivier.roux@ird.fr

Project developed as part of a Master's thesis on mosquito behavior analysis.
