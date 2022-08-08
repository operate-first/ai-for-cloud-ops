# Praxi iPython Magic
Praxi Magic is a iPython magic command that allows users to run Praxi directly from Jupyter Notebook to discover unwanted cloud software.

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
## Installataion
1. add the `extensions` directory into `~./ipython directory`
2. update the ipython config file located at `~/.ipython/profile_default/ipython_config.py` by uncommenting the extension configuration and adding `"praxi"` or replace the config file entirely. This will load Praxi Magic into your notebook everytime a new iPython kernel is started.
3. or manually load Praxi Magic into Jupyter Notebook by using the magic command `%load_ext praxi`
4. Praxi Magic is now ready to be run!

## Use Cases
