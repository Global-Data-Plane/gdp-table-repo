API_ROUTES = [
    {
        "route": "/tables",
        "methods": ["GET"],
        "parameters": [],
        "description": "List all table names the user can access. Keys are returned."
    },
    {
        "route": "/upload/<name>",
        "methods": ["POST"],
        "parameters": ["table"],
        "description": "Upload a table in the table argument to the GDP repository. Returns the key of the uploaded table."
    },
    {
        "route": "/table/<key>",
        "methods": ["GET"],
        "parameters": [],
        "description": "Returns the table with key <key>, as an SDML object."
    },
    {
        "route": "/delete/<name>",
        "methods": ["DELETE"],
        "parameters": [],
        "description": "Delete the table with name <name>. Only the owner of the table can call this."
    },
    {
        "route": "/share/<name>",
        "methods": ["POST"],
        "parameters": ["share"],
        "description": "Share the table with name <name> with users in the list share. Note the contents of this list replaces the previous share. Only the owner of the table can call this."
    },
    {
        "route": "/get_table_names",
        "methods": ["GET"],
        "parameters": [],
        "description": "List all table names the user can access. Keys are returned."
    },
    {
        "route": "/get_tables",
        "methods": ["GET"],
        "parameters": [],
        "description": "Get a dictionary <key>: <schema> of all the tables the user can access."
    },
    {
        "route": "/get_table_schema",
        "methods": ["GET"],
        "parameters": ["table"],
        "description": "Get the schema for the table with key <table>."
    },
    {
        "route": "/get_range_spec",
        "methods": ["GET"],
        "parameters": ["table", "column"],
        "description": "Return the minimum and maximum values of the column as a list."
    },
    {
        "route": "/get_all_values",
        "methods": ["GET"],
        "parameters": ["table", "column"],
        "description": "Get all the values from column."
    },
    {
        "route": "/get_column",
        "methods": ["GET"],
        "parameters": ["table", "column"],
        "description": "Get all the values from column."
    },
    {
        "route": "/get_filtered_rows",
        "methods": ["POST"],
        "parameters": ["table", "columns (optional)", "filter_spec (optional)", "format (optional)"],
        "description": "Filter the rows according to the specification given by filter_spec. Returns the rows for which the resulting filter returns True. If columns is specified, return only those columns. Return in the format specified by format. If 'dict', return a list of dictionaries; if 'SDML', return a RowTable; if 'list' or omitted, return a list of lists of values."
    },
]
