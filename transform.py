import json
from dateutil.parser import parse
from importlib_metadata import metadata
import pandas as pd

class JiraIssue():
    '''jira ticket instance that has some descriptive fields, 
    an extract of history and a data_dict
    '''
    def __init__(self, metadata, history):
        self.issue_key = metadata['issue_key']
        self.summary = metadata['summary']
        self.issue_type = metadata['issue_type']
        self.implementer = metadata['implementer']
        self.fix_version = metadata['fix_version']
        self.issue_size = metadata['issue_size']
        self.team = metadata['team']
        self.parent = metadata['parent']
        self.project = metadata['project']
        self.history = history
        self.data_dict = metadata

    def calc_time(self):
        print(f'processing {self.issue_key}')
        """iterate thru a list of status change events and calc time
        populates a data_dict member of the instance with time for each stat"""
        statuses = set()
        self.history[0]['to'] = self.history[1]['from']
        self.data_dict['ready_time'] = 'None'
        for val in self.history:
            status = val['to']
            statuses.add(status)
            self.data_dict[status] = 0         
        for index, val in enumerate(self.history):
            if val['from'] == 'void':
                self.data_dict['created_time'] = val['time_stamp']
            else:
                if val['to'] == 'Ready':
                    self.data_dict['ready_time'] = val['time_stamp']
                status_name = val['from']
                time_event = parse(val['time_stamp'])
                time_prev = parse(self.history[index-1]['time_stamp'])
                self.data_dict[status_name] = self.data_dict[status_name] + \
                    (time_event - time_prev).total_seconds()
        self.data_dict['created_time'] = parse_date(
            self.data_dict['created_time'])
        if self.data_dict['ready_time'] != 'None':
            self.data_dict['ready_time'] = parse_date(
                self.data_dict['ready_time'])
        for val in statuses:
            if self.data_dict[val] > 0:
                self.data_dict[val] = round((self.data_dict[val]/3600), 2)

    def __repr__(self):
        return f"{self.data_dict}"


def parse_date(date, fmt=None):
    '''
    converts data from a long timestamp to a better one
    '''
    if fmt is None:
        fmt = '%Y-%m-%d %H:%M:%S'
    get_date_obj = parse(str(date))
    return str(get_date_obj.strftime(fmt))


def dump_to_csv(issues_list):
    '''
    iterate over issues list and append them one by one to a dataframe, save
    data frame on the drive
    '''
    df = pd.DataFrame()
    for issue in issues_list:
        df = df.append(issue.data_dict, ignore_index=True)
    df['created_time'] = pd.to_datetime(df['created_time'])
    df.to_csv('output.csv', index=False)


def main():

    with open('json_data.json') as json_file:
        data = json.load(json_file)        
    issue_list = []
    for list_item in data:
        metadata=list_item['metadata']
        history = list_item['history']
        issue = JiraIssue(metadata,history)
        issue.calc_time()
        issue_list.append(issue)
    dump_to_csv(issue_list)

if __name__ == "__main__":
    main()
