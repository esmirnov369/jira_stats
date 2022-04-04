from jira import JIRA
from datetime import datetime
from dateutil.parser import parse 
import creds
import pandas as pd 
import numpy as np 
from sqlalchemy import create_engine

class jira_issue():
    def __init__(self, metadata,history,flag_count,flags_expl_list):
        self.issue_key = metadata['issue_key']
        self.summary = metadata['summary']
        self.issuetype = metadata['issuetype']
        self.implementer = metadata['implementer']
        self.fixVersion = metadata['fixVersion']
        self.epicLink = metadata['epicLink']
        self.issueSize = metadata['issueSize']
        self.history = history
        self.data_dict = metadata
        self.flag_count = flag_count
        self.flags_expl_list = flags_expl_list
    def calc_time(self):
        statuses = []
        self.history[0]['to'] = self.history[1]['from']
        for val in self.history:   
            status = val['to']
            statuses.append(status)
            self.data_dict[status] = 0
            self.data_dict['ready_time'] = 'None'
        for index,val in enumerate(self.history):
            if val['from'] == 'void':
                self.data_dict['created_time'] = val['time_stamp']   
            else:
                if val['to'] == 'Ready':
                    self.data_dict['ready_time'] = val['time_stamp']     
                status_name = val['from']
                time_event =  parse(val['time_stamp'])
                time_prev = parse(self.history[index-1]['time_stamp'])
                self.data_dict[status_name] =  self.data_dict[status_name] + (time_event - time_prev).total_seconds()
        self.data_dict['created_time'] = parse_date_convert(self.data_dict['created_time'])
        if self.data_dict['ready_time'] != 'None':
            self.data_dict['ready_time'] = parse_date_convert(self.data_dict['ready_time']) 
        
            
        status_set = set(statuses)
        for val in status_set:
           if self.data_dict[val] > 0:
               self.data_dict[val] = round(self.data_dict[val]/3600, 2)

    def parse_flags(self):
        self.data_dict['nflags'] = self.flag_count
        for comment in range(len(self.flags_expl_list)):
            key = 'flag_comment' + str(comment)
            comment_text = self.flags_expl_list[comment]          
            self.data_dict[key] = comment_text
        print( self.data_dict)    
    def __repr__(self):
        return f"{self.data_dict}"

def parse_date_convert(date, fmt=None):
    if fmt is None:
        fmt = '%Y-%m-%d %H:%M:%S' 
    get_date_obj = parse(str(date))
    return str(get_date_obj.strftime(fmt))



#gets one issue by key, parses transitions, calls time calc function
def populate_issue_obj(issue_key,jira_instance):

    issue = jira_instance.issue(issue_key,expand='changelog')
    summary = issue.fields.summary
    issuetype = issue.fields.issuetype.name
    try:
        implementer = issue.fields.customfield_10502.displayName
    except:
        implementer = "NA"
    try:
        fixVersion = issue.fields.fixVersions[0].name    
    except:
        fixVersion = "NA"
    try:    
        epicLink = issue.fields.customfield_11914
    except:
        epicLink = "NA"
    try:    
        issueSize = issue.fields.customfield_169100
    except:
        issueSize = "NA"          
    transact_list = []
    transact_list.append({'to':'CREATION','from':'void','time_stamp':issue.fields.created})
    flags_expl_list = []
    flag_count = 0
    for history in issue.changelog.histories:     
        change_dict = {}
        change_dict['to'] = ''
        change_dict['from'] = ''
        for item in history.items:
            if item.field == "status":
                change_dict['time_stamp'] = history.created
                change_dict['from'] =  (item.fromString) # new value
                change_dict['to'] =  (item.toString) # new value
                transact_list.append(change_dict)
            if item.field == "Flagged":
                flag_count = flag_count + 1
                flag_time = parse(history.created)
                for comment in issue.fields.comment.comments: 
                    time_comment = parse(comment.created)
                    duration = (time_comment - flag_time ).total_seconds()
                    if duration < 1 and duration > 0 and comment.body[0:6] == '(flag)':
                        reason = comment.body.replace('\n'," ")
                        reason = reason.replace('\r'," ")
                        flags_expl_list.append(reason)
    issue_meta = {'issueSize':issueSize,'fixVersion':fixVersion, 'epicLink': epicLink, 'issue_key':issue_key,'summary':summary,'issuetype':issuetype,'implementer':implementer}
    issue_object = jira_issue(metadata= issue_meta,history=transact_list,flag_count=flag_count,flags_expl_list = flags_expl_list)
    issue_object.calc_time()
    issue_object.parse_flags()    
    return issue_object


def dump_to_csv(issues_list,jira):
    df = pd.DataFrame()    
    for issue in issues_list:
        print(f"starting on {issue.key}")
        issue_object = populate_issue_obj(issue.key,jira)
        df = df.append(issue_object.data_dict, ignore_index=True)
        print(f"{issue.key} is processed")
    df['created_time']= pd.to_datetime(df['created_time'])
    try:
        df['ready_time']= pd.to_datetime(df['ready_time'])
    except:
        pass          
    df.to_csv('out.csv',index=False)
 


def main():
    jira_options = creds.options
    login = creds.email
    passw = creds.passw
    jira = JIRA(options=jira_options, basic_auth=(login, passw))
    try:   
        jql_query = creds.jql
        issues_list = jira.search_issues(jql_query,maxResults=400) 
    except:
        print('JQL or Auth error')
        return

    dump_to_csv(issues_list,jira)
    

if __name__ == "__main__":
    main()
    