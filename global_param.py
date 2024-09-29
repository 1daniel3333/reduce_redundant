#file folder of your saving file or logs
directory = 'c:\\Users\\Dell\\Documents\\reduce_redundant\\log_file'
#header of string (upper and lower case need to match) of the partial column name
col_header = 'LOT'
# ???
column_to_keep = ['LOT','waferID','DieX','DieY'] #keep only wafer
#fail type hash, format is key as bigger group with value is a list of smaller group
fail_type_map = {
    'TYPE1': ['SB', 'HTB'], 
    'TYPE2':['VTB','BL']
}