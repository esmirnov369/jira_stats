import pandas as pd 
import numpy as np 
def main():

    settings = {}
    df = pd.read_csv('output.csv')
    settings['MBcycle_column_names'] = ['Ready to Develop','In Progress','Review','Automation','Test Review','Resolved','Ready for Testing','Testing','Ready for Design Review','Design Review',]
    settings['MBactive_column_names'] = ['In Progress','Review','Automation','Test Review','Testing','Design Review',]
    settings['MBpassive_column_names'] = ['Ready to Develop','Resolved','Ready for Testing','Ready for Design Review']
    
    settings['APIcycle_column_names'] = ['Planned','Specification Review', 'ToDo', 'Ready to Develop','In Progress','Review','Resolved','Testing']
    settings['APIactive_column_names'] = ['Specification Review','In Progress','Review','Testing']
    settings['APIpassive_column_names'] = ['Planned', 'ToDo', 'Ready to Develop','Resolved']
    settings['APIlead_column_names'] = ['Planned','Specification Review', 'ToDo', 'Ready to Develop','In Progress','Review','Resolved','Testing']
    projects = df['project'].unique()

    df['Cycle_RTD_hours']= df[settings['APIcycle_column_names']].sum(axis=1)
    df['active_time'] = df[settings['APIactive_column_names']].sum(axis=1)
    df['passive_time'] = df[settings['APIpassive_column_names']].sum(axis=1)
    df['flow_efficiency'] = (df['active_time']/df['Cycle_RTD_hours'])*100
    df['Cycle_RTD_days'] = df['Cycle_RTD_hours']/24
    df['ready_time'] = pd.to_datetime(df.ready_time)   

    bugs_df = df[df['parent'].str.len() > 0]
    bugs_df = (bugs_df.groupby(by="parent").size())
    combo = pd.merge(df,bugs_df.rename('defects'),how='left',left_on=['issue_key'],right_on=['parent'])
    combo.to_csv('Reporting/api_metrics.csv',index = False)


if __name__ == "__main__":
    main()


