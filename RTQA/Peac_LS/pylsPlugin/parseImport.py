import ast
# from collections import namedtuple
# from webbrowser import get

# Below line is commented out because didn't see a reason to create a collection with namedtuple
# Can be added back if that is wanted
# Definition 
# Import = namedtuple("Imports", ["module", "name", "alias", "lineno", "col_offset", "end_col_offset"])

# Function 
def get_imports(path):
    """ 
    Using ast from standard python libaries to find all the modules that is imported
    in the current code cell (put in to the function through the plugin)
    """
    results = []
    root = ast.parse(path.read())

    for node in ast.iter_child_nodes(root):
        
        if isinstance(node, ast.Import):
            module = []
        elif isinstance(node, ast.ImportFrom):  
            module = node.module.split('.')
        else:
            continue
        
        lineno = node.lineno
        col_offset = node.col_offset
        end_col_offset = node.end_col_offset
        
        for n in node.names:
            results.append([module, n.name.split('.'), n.asname, lineno, col_offset, end_col_offset])

    return results 