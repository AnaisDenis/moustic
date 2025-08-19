# Installation of moustic

### Step 1 : Retrieve this file containing the codes and test 

[Download moustic as a ZIP file](https://github.com/AnaisDenis/moustic/archive/refs/heads/main.zip)

You can extract this folder to the directory of your choice: you will find the .zip file in your downloads. Move it by right-clicking, cutting, and pasting it into the directory of your choice. Then right-click and extract here.

### Step 2: Open a terminal
A terminal (or command prompt) is a tool that allows you to interact with your computer by typing text commands. Unlike a graphical interface (where you click buttons), the terminal allows you to execute specific instructions, such as launching a Python script, installing libraries, or navigating through your project folders.

**Windows**: Press Windows + R, type cmd, and then press Enter.

**macOS**: Open the Terminal application via Spotlight (Cmd + Space, then type "Terminal").

**Linux**: Use the shortcut Ctrl + Alt + T or search for "Terminal" in your applications menu.

To install moustic, you need Python 

### Step 3: Check if Python is Installed

Type the following command:

	python --version

or 

	python3 --version

If you see something like Python 3.x.x, Python is already installed. Otherwise, proceed to the next step.

### Step 4 : Install Python

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

### Step 5 : Install pip (if not already installed)

Most modern Python installations include pip. To check:

	pip --version

or

	pip3 --version

If it's missing:

On Windows, reinstall Python and ensure "Install pip" is checked

On Linux, use:

	sudo apt install python3-pip

### Step 6: Virtual Environment

It is recommended to use a virtual environment:

- Each virtual environment contains its own version of Python and its own packages, independent of other projects or the system installation. This prevents a package update for one project from breaking another.
- You can install exactly the versions of libraries needed for one project without affecting others. Perfect for replicating an environment on another machine.

In your terminal you need to move to the moustic-main directory
You must write in your terminal: 
	
 	cd <path_to_moustic>

Example:

cd /Users/alex/Downloads/moustic-main

**Note**: To find your path:
Open File Explorer.
Go to your project folder.
Click in the address bar at the top: the path will appear.

Then, copy :

	python -m venv env

This creates an env/ folder containing an isolated Python installation.

Then you need to activate your virtual environment. Type always in your terminal :

**For Windows**

	.\env\Scripts\activate

**For Linux/macOS**

	source env/bin/activate

Normally you should see your virtual environment name displayed in parentheses at the beginning of the new command line

### Retrieve this file containing the codes and test 

[Download moustic as a ZIP file](https://github.com/AnaisDenis/moustic/archive/refs/heads/main.zip)

You can extract this folder to the directory of your choice: you will find the .zip file in your downloads. Move it by right-clicking, cutting, and pasting it into the directory of your choice. Then right-click and extract here.

### Step 7: Install moustic

Once your virtual environment is activated and you are in the project directory (the folder that contains `pyproject.toml`), install moustic and its dependencies with:

    pip install .

This command will install:
- the `moustic` tool,
- all required dependencies

### Step 8: Open moustic

Now, if you copy and paste in your terminal : 

    python app.py

You should see a URL like this: http://127.0.0.1:8050/
You can click on it if it appears interactive. Otherwise, copy and paste this URL into your browser.

Congratulations ! You can use moustic ! Next time, just repeat steps 2, 6, and 8

Note: The Moustic app allows you to download swarm videos. This feature requires downloading an application (see Install FFMPEG section).
### Step 9: Install FFMPEG

To download ffmpeg.exe, you can download the file in .7z [here]( https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.7z)
Or, you can download the file in .zip [here](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip)

Next, you need to unzip the downloaded file. Open the ffmpeg folder, then the bin folder. Copy the ffmpeg.exe file and paste it into the bin file located in the moustic-main folder.


