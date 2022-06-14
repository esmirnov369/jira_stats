import pandas as pd

def dump_to_csv(issues_list):
    '''
    iterate over issues list and append them one by one to a dataframe, save
    data frame on the drive
    '''
    df = pd.DataFrame()
    for issue in issues_list:
        df = df.append(issue.data_dict, ignore_index=True)
    df['created_time'] = pd.to_datetime(df['created_time'])
    try:
        df['ready_time'] = pd.to_datetime(df['ready_time'])
    except:
        df['ready_time'] = "NA"
    df.to_csv('out.csv', index=False)
