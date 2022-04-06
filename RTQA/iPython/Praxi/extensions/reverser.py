from IPython.core.magic import (register_line_magic, register_cell_magic, register_line_cell_magic)
from notebook.services.config import ConfigManager
from IPython.utils.timing import clock, clock2

def load_ipython_extension(ipython):
    @register_line_magic("brianreverse")
    def lmagic(line):
        "Line magic that reverses any string that is passed"
        return line[::-1] 

    @register_line_cell_magic("briantest")
    def lcmagic(self, line, cell):
        "Magic that works both as %lcmagic and as %%lcmagic"
        if cell is None:
            print("Called as line magic")
            return line
        else:
            print("Called as cell magic")
            return line, cell