import ast
import os
import sys
import time
import math
import subprocess
import shlex
import argparse
from ast import Module

from IPython.core import magic_arguments, oinspect, page
from IPython.core.error import UsageError
from IPython.core.macro import Macro
from IPython.core.magic import (
    Magics,
    cell_magic,
    line_cell_magic,
    line_magic,
    magics_class,
    needs_local_scope,
    no_var_expand,
    on_off,
)
from IPython.testing.skipdoctest import skip_doctest
from IPython.utils.capture import capture_output
from IPython.utils.contexts import preserve_keys
from IPython.utils.ipstruct import Struct
from IPython.utils.module_paths import find_mod
from IPython.utils.path import get_py_filename, shellglob
from IPython.utils.timing import clock, clock2

@magics_class
class ExecutionMagics(Magics):
    """Magics related to code execution, debugging, profiling, etc.
    """

    def __init__(self, shell):
        super(ExecutionMagics, self).__init__(shell)
        # Default execution function used to actually run user code.
        self.default_runner = None

    @line_cell_magic
    def abracadabra(self, line, cell=None):
        "Magic that works both as %lcmagic and as %%lcmagic"
        if cell is None:
            print("Called as line magi")
            return line
        else:
            print("Called as cell magic")
            return line, cell

    @skip_doctest
    @no_var_expand
    @needs_local_scope
    @line_cell_magic
    def praxi(self,line='', cell=None, local_ns=None):
        print("Starting praxi magic")
        # p = subprocess.Popen(['python', './.ipython/extensions/cs_rec.py','-t','.','-l','hello'], stdin=subprocess.PIPE, shell=True)
        
        # We are assuming cs_rec.py placed next to praxiMagic.py
        dirname = os.path.dirname(__file__)
        # For now assume we ONLY use this as cell magic
        p = subprocess.Popen(['python', os.path.join(dirname, 'cs_rec.py')] + shlex.split(line), stdin=subprocess.PIPE, shell=True)
        
        # os.system("python ./.ipython/extensions/cs_rec.py -t . -l hello")

        # fail immediately if the given expression can't be compiled
        # if line and cell:
        #     raise UsageError("Can't use statement directly after '%%time'!")

        if cell:
            expr = self.shell.transform_cell(cell)
        else:
            expr = self.shell.transform_cell(line)

        # Minimum time above which parse time will be reported
        tp_min = 0.1

        t0 = clock()
        expr_ast = self.shell.compile.ast_parse(expr)
        tp = clock()-t0

        # Apply AST transformations
        expr_ast = self.shell.transform_ast(expr_ast)

        # Minimum time above which compilation time will be reported
        tc_min = 0.1

        expr_val=None
        if len(expr_ast.body)==1 and isinstance(expr_ast.body[0], ast.Expr):
            mode = 'eval'
            source = '<timed eval>'
            expr_ast = ast.Expression(expr_ast.body[0].value)
        else:
            mode = 'exec'
            source = '<timed exec>'
            # multi-line %%time case
            if len(expr_ast.body) > 1 and isinstance(expr_ast.body[-1], ast.Expr):
                expr_val= expr_ast.body[-1]
                expr_ast = expr_ast.body[:-1]
                expr_ast = Module(expr_ast, [])
                expr_val = ast.Expression(expr_val.value)

        t0 = clock()
        code = self.shell.compile(expr_ast, source, mode)
        tc = clock()-t0

        # skew measurement as little as possible
        glob = self.shell.user_ns
        wtime = time.time
        # time execution
        wall_st = wtime()
        if mode=='eval':
            st = clock2()
            try:
                out = eval(code, glob, local_ns)
            except:
                self.shell.showtraceback()
                return
            end = clock2()
        else:
            st = clock2()
            try:
                exec(code, glob, local_ns)
                out=None
                # multi-line %%time case
                if expr_val is not None:
                    code_2 = self.shell.compile(expr_val, source, 'eval')
                    out = eval(code_2, glob, local_ns)
            except:
                self.shell.showtraceback()
                return
            end = clock2()

        wall_end = wtime()
        # Compute actual times and report
        wall_time = wall_end - wall_st
        cpu_user = end[0] - st[0]
        cpu_sys = end[1] - st[1]
        cpu_tot = cpu_user + cpu_sys
        # On windows cpu_sys is always zero, so only total is displayed
        if sys.platform != "win32":
            print(
                f"CPU times: user {_format_time(cpu_user)}, sys: {_format_time(cpu_sys)}, total: {_format_time(cpu_tot)}"
            )
        else:
            print(f"CPU times: total: {_format_time(cpu_tot)}")
        print(f"Wall time: {_format_time(wall_time)}")
        if tc > tc_min:
            print(f"Compiler : {_format_time(tc)}")
        if tp > tp_min:
            print(f"Parser   : {_format_time(tp)}")

        p.communicate(input=b'\n')
        return out

def _format_time(timespan, precision=3):
    """Formats the timespan in a human readable form"""

    if timespan >= 60.0:
        # we have more than a minute, format that in a human readable form
        # Idea from http://snipplr.com/view/5713/
        parts = [("d", 60*60*24),("h", 60*60),("min", 60), ("s", 1)]
        time = []
        leftover = timespan
        for suffix, length in parts:
            value = int(leftover / length)
            if value > 0:
                leftover = leftover % length
                time.append(u'%s%s' % (str(value), suffix))
            if leftover < 1:
                break
        return " ".join(time)

    
    # Unfortunately the unicode 'micro' symbol can cause problems in
    # certain terminals.  
    # See bug: https://bugs.launchpad.net/ipython/+bug/348466
    # Try to prevent crashes by being more secure than it needs to
    # E.g. eclipse is able to print a µ, but has no sys.stdout.encoding set.
    units = [u"s", u"ms",u'us',"ns"] # the save value   
    if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:
        try:
            u'\xb5'.encode(sys.stdout.encoding)
            units = [u"s", u"ms",u'\xb5s',"ns"]
        except:
            pass
    scaling = [1, 1e3, 1e6, 1e9]
        
    if timespan > 0.0:
        order = min(-int(math.floor(math.log10(timespan)) // 3), 3)
    else:
        order = 3
    return u"%.*g %s" % (precision, timespan * scaling[order], units[order])

def load_ipython_extension(ipython):
    """
    Any module file that define a function named `load_ipython_extension`
    can be loaded via `%load_ext module.path` or be configured to be
    autoloaded by IPython at startup time.
    """
    # This class must then be registered with a manually created instance,
    # since its constructor has different arguments from the default:
    magics = ExecutionMagics(ipython)
    ipython.register_magics(magics)