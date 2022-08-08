# Praxi iPython Magic
RTQA Praxi Magic is a iPython magic command that allows users to run [Praxi](https://github.com/peaclab/praxi) directly from Jupyter Notebook to discover unwanted cloud software.

## Usage
Run Praxi as a line magic:
```
%praxi !pip install <package-to-be-installed>
```
as a cell magic:
```
%%praxi
!pip install <package-to-be-installed>
```
## Installation
1. Ensure your system's up to date: `sudo apt update && sudo apt upgrade`
2. Install PIP and ensure it's up to date: `sudo apt install python3-pip && sudo pip3 install --upgrade pip`
3. Install (or update) dependencies: `sudo pip3 install --upgrade watchdog numpy scipy sklearn tqdm envoy`
4. Add the `extensions` directory into `~./ipython directory`
5. Update the ipython config file located at `~/.ipython/profile_default/ipython_config.py` by uncommenting the extension configuration and adding `"praxi"` or replace the config file entirely. This will load Praxi Magic into your notebook everytime a new iPython kernel is started.
6. **OR** manually load Praxi Magic into Jupyter Notebook by using the magic command `%load_ext praxi`
7. Praxi Magic is now ready to be run!

## Repository Organization
* **changesets**: contains changesets generated from running shell command
* **tagsets**: contains tagsets generated from `/changesets`. Used as an input to make a prediction of what was installed.
* **cs_recorder**: code for recording changesets.
* **demo_tagsets**: contains previously generated tagsets, which are used to create a model for predicting installed packages. 
* **columbus**: Columbus code used to generate tagsets from changesets.

Please refer to the [Praxi Wiki](https://github.com/peaclab/praxi/wiki) for more in-depth information.
