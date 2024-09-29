#file folder of your saving file or logs
directory = 'c:\\Users\\Dell\\Documents\\reduce_redundant\\log_file'
#header of string (upper and lower case need to match) of the partial column name
col_header = 'LOT'
# ???
wafer_name = 'waferID'
die_x_name = 'DieX'
die_y_name = 'DieY'
column_to_keep = [die_x_name,die_y_name,wafer_name]
#fail type hash, format is key as bigger group with value is a list of smaller group
fail_type_map = {
    'TYPE1': ['SB', 'HTB'], 
    'TYPE2':['VTB','BL']
}
# Define the range for DieX and DieY
die_X_range = range(-5, 6)
die_Y_range = range(-4, 5)