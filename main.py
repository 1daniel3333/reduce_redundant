import os
import pandas as pd
import global_param as param

def get_decode_raw_file(file_list, col_header:str=param.col_header)->pd.DataFrame:
    merging_list = []
    for file_name in file_list:
        file_location = os.path.join(param.directory, file_name)
        # Open the file in read mode
        find_header = False
        content = [] #format [[1,2,LOT.X3],[1,2,LOT.X2],[1,2,LOT.X1]]
        header = [] #format [DieX, DieY, Wafer,...]

        with open(file_location, 'r') as file:
            # Read the file line by line
            for line in file:
                if find_header:
                    content.append(line.strip().split())
                else:
                    if col_header in line.strip():
                        find_header = True
                        header = line.strip().split()
            if len(header)!=len(content[0]):
                raise ValueError('Length not match!')
        df = pd.DataFrame(content, columns=header)
        merging_list.append(df)
    merged_df = pd.concat(merging_list, ignore_index=True)
    return merged_df

def group_data(df:pd.DataFrame, fail_map:dict)->pd.DataFrame:
    print(f'You dataframe column had {list(df.columns)}')
    for new_col, cols_to_sum in fail_map.items():
        for single_col in cols_to_sum:
            if single_col not in list(df.columns):
                raise ValueError(f'Column name {single_col} not in column name')
        df[new_col] = df[cols_to_sum].astype(int).sum(axis=1)

    #kepp wanted column
    fin_col_to_keep = list(set(list(fail_map.keys()) + list(param.column_to_keep)))
    return df[fin_col_to_keep]

def pivot_wide_table_to_long(df:pd.DataFrame, fail_map:dict)->pd.DataFrame:
    # Group by DieY, waferID, LOT, DieX
    grouped_df = df.groupby(param.column_to_keep).first().reset_index()

    # Pivot TYPE1 and TYPE2 from wide table to long table
    long_df = pd.melt(grouped_df, id_vars=param.column_to_keep, value_vars=list(fail_map.keys()), var_name='FAIL_TYPE', value_name='VALUE')
    return long_df

def backfill_dummy(df:pd.DataFrame, fail_map:dict)->pd.DataFrame:
    #define columns to create dummy
    columns_to_group = param.column_to_keep+ ['FAIL_TYPE']
    
    #change to int format
    for name in [param.die_x_name,param.die_y_name]:
        df[name] = df[name].astype(int)
        
    #clean unwanted column
    column_to_keep_local = columns_to_group + ['VALUE']
    df = df[column_to_keep_local]
    
    # Create a MultiIndex for all combinations of DieX and DieY
    index = pd.MultiIndex.from_product([param.die_X_range, param.die_Y_range,list(df[param.wafer_name].unique()),list(fail_map.keys())], names=columns_to_group)

    df = df.drop_duplicates(subset=columns_to_group)
    df = df.set_index(columns_to_group).reindex(index).reset_index()
    return df

def gen_1st_level_to_result_checking(df:pd.DataFrame):
    # Pivot the DataFrame
    pivot_df = df.pivot_table(index=[param.wafer_name, param.die_y_name, 'FAIL_TYPE'], columns=[param.die_x_name], values='VALUE').reset_index()
    pivot_df.columns.name = None
    # pivot_df = pivot_df.sort_values(by=['FAIL_TYPE', param.die_y_name], ascending=[True, False])
    return pivot_df

def gen_pivot_to_wide_form_by_wafer(df:pd.DataFrame)->pd.DataFrame:
    # Set DieY and FAIL_TYPE as index
    df.set_index(['FAIL_TYPE',param.die_y_name], inplace=True)

    # Group by waferID and save to CSV
    grouped_df = df.groupby(param.wafer_name)

    # Create a new DataFrame to store the combined result
    combined_df = pd.DataFrame()

    # Iterate over each group and concatenate them into the combined DataFrame
    for name, group in grouped_df:
        group = group.drop(columns=param.wafer_name)
        group.columns = pd.MultiIndex.from_product([[name], group.columns])
        
        # Create a DataFrame with the same shape as group but filled with None
        none_df = pd.DataFrame(None, index=group.index, columns=group.columns)
        
        # Combine combined_df and group, preserving None values
        combined_df = pd.concat([combined_df, none_df], axis=1).combine_first(group)

    combined_df = combined_df.sort_values(by=['FAIL_TYPE', param.die_y_name], ascending=[True, False])
    combined_df = combined_df.reset_index()

    # Rename columns
    combined_df = combined_df.rename(columns={param.die_y_name: 'Fail_%',})
    return combined_df

def add_x_col_in_df(df:pd.DataFrame)->pd.DataFrame:
    # Copy the first row
    first_row = df.iloc[0]

    # Find the indices where FAIL_TYPE changes
    change_indices = df[df['FAIL_TYPE'].ne(df['FAIL_TYPE'].shift())].index

    # Create a list to store the new DataFrame rows
    new_rows = []

    # Iterate over the DataFrame and insert the copied row at the change points
    for i in range(len(df)):
        if i in change_indices and i != 0:
            new_rows.append(first_row)
        new_rows.append(df.iloc[i])

    # Create a new DataFrame from the new rows
    new_df = pd.DataFrame(new_rows).reset_index(drop=True)
    remove_index_0= new_df.drop(index=0).reset_index(drop=True)
    return remove_index_0

# Get the list of all files
file_list = [f for f in os.listdir(param.directory) if os.path.isfile(os.path.join(param.directory, f))]
print(f'Selected file name is {file_list}')


#fail mode raw data to a clean data format
first_level_df = get_decode_raw_file(file_list)
first_level_df.to_csv('first_level_df.csv', index=False)

second_level_data = group_data(first_level_df, param.fail_type_map)
second_level_data.to_csv('second_level_data.csv', index=False)

long_table_raw = pivot_wide_table_to_long(second_level_data, param.fail_type_map)
long_table = backfill_dummy(long_table_raw, param.fail_type_map)
long_table.to_csv('long_table.csv', index=False)

#get fail data type to a user friendly view
result_check_1st_raw = gen_1st_level_to_result_checking(long_table)
result_check_1st_raw.to_csv('result_check_1st_raw.csv', index=False)

combined_df = gen_pivot_to_wide_form_by_wafer(result_check_1st_raw)
combined_df.to_csv('grouped.csv', index=False)

viewing_last_df = pd.read_csv('grouped.csv')
fin_df = add_x_col_in_df(viewing_last_df)
fin_df.to_csv('fin_table.csv', index=False)
print('Run success!')