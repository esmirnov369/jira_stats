from jira import JIRA
from dateutil.parser import parse
import pandas as pd
import creds


settings = {'parse_flags': False}


class JiraIssue():
    '''jira ticket instance that has some descriptive fields, 
    an extract of history and a data_dict
    '''
    def __init__(self, metadata, history, flag_count, flags_expl_list):
        self.issue_key = metadata['issue_key']
        self.summary = metadata['summary']
        self.issuetype = metadata['issuetype']
        self.implementer = metadata['implementer']
        self.fix_version = metadata['fixVersion']
        self.issue_size = metadata['issueSize']
        self.history = history
        self.data_dict = metadata
        self.flag_count = flag_count
        self.flags_expl_list = flags_expl_list

    def calc_time(self):
        """iterate thru a list of status change events and calc time
        populates a data_dict member of the instance with time for each stat"""
        statuses = []
        self.history[0]['to'] = self.history[1]['from']
        for val in self.history:
            status = val['to']
            statuses.append(status)
            self.data_dict[status] = 0
            self.data_dict['ready_time'] = 'None'
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
        self.data_dict['created_time'] = parse_date_convert(
            self.data_dict['created_time'])
        if self.data_dict['ready_time'] != 'None':
            self.data_dict['ready_time'] = parse_date_convert(
                self.data_dict['ready_time'])

        status_set = set(statuses)
        for val in status_set:
            if self.data_dict[val] > 0:
                self.data_dict[val] = round(self.data_dict[val]/3600, 2)

    def parse_flags(self):
        '''
        count flag instances and try to get a comment for each 
        if a flag was added with a comment
        '''
        self.data_dict['nflags'] = self.flag_count
        for comment in range(len(self.flags_expl_list)):
            key = 'flag_comment' + str(comment)
            comment_text = self.flags_expl_list[comment]
            self.data_dict[key] = comment_text
        print(self.data_dict)

    def __repr__(self):
        return f"{self.data_dict}"


def parse_date_convert(date, fmt=None):
    '''
    converts data from a long timestamp to a better one
    '''
    if fmt is None:
        fmt = '%Y-%m-%d %H:%M:%S'
    get_date_obj = parse(str(date))
    return str(get_date_obj.strftime(fmt))


# gets one issue by key, parses transitions, calls time calc function
def populate_issue_obj(issue_key, jira_instance):

    issue = jira_instance.issue(issue_key, expand='changelog')
    summary = issue.fields.summary
    issuetype = issue.fields.issuetype.name
    implementer = issue.fields.customfield_10502.displayName if issue.fields.customfield_10502 else "N/A"
    fix_version = issue.fields.fixVersions[0].name if issue.fields.fixVersions else "N/A"
    issue_size = issue.fields.customfield_169100.value if issue.fields.customfield_169100 else "NA"
    transact_list = []
    transact_list.append({'to': 'CREATION', 'from': 'void',
                         'time_stamp': issue.fields.created})
    flags_expl_list = []
    flag_count = 0
    for history in issue.changelog.histories:
        change_dict = {}
        change_dict['to'] = ''
        change_dict['from'] = ''
        for item in history.items:
            if item.field == "status":
                change_dict['time_stamp'] = history.created
                change_dict['from'] = (item.fromString)  # new value
                change_dict['to'] = (item.toString)  # new value
                transact_list.append(change_dict)
            if item.field == "Flagged":
                flag_count = flag_count + 1
                flag_time = parse(history.created)
                for comment in issue.fields.comment.comments:
                    time_comment = parse(comment.created)
                    duration = (time_comment - flag_time).total_seconds()
                    if duration < 1 and duration > 0 and comment.body[0:6] == '(flag)':
                        reason = comment.body.replace('\n', " ")
                        reason = reason.replace('\r', " ")
                        flags_expl_list.append(reason)
    issue_meta = {'issueSize': issue_size, 'fixVersion': fix_version,  'issue_key': issue_key,
                  'summary': summary, 'issuetype': issuetype, 'implementer': implementer}
    issue_object = JiraIssue(metadata=issue_meta, history=transact_list,
                              flag_count=flag_count, flags_expl_list=flags_expl_list)
    issue_object.calc_time()
    if settings['parse_flags']:
        issue_object.parse_flags()
    return issue_object


def dump_to_csv(issues_list):
    '''
    iterate over issues list and append them one by one to a dataframe, save
    data frame on the drive
    '''
    df = pd.DataFrame()
    for issue in issues_list:
        df = df.append(issue.data_dict, ignore_index=True)
    df['created_time'] = pd.to_datetime(df['created_time'])
    df['ready_time'] = pd.to_datetime(df['ready_time']) if df['ready_time'] else "N/A"
    df.to_csv('out.csv', index=False)


def get_raw_data(issues_list, jira):
    '''
    run over a big list of issues and pull bits of history transitions
    for every issues
    '''
    data_issue_list = []
    for issue in issues_list:
        issue_object = populate_issue_obj(issue.key, jira)
        data_issue_list.append(issue_object)
    return data_issue_list


def main():
    '''it's main yo'''
    jira_options = creds.options
    login = creds.email
    passw = creds.passw
    jira = JIRA(options=jira_options, basic_auth=(login, passw))
    try:
        jql_query = creds.jql
        issues_list = jira.search_issues(jql_query, maxResults=10)
    except:
        print('JQL or Auth error')
        return
    populated_list = get_raw_data(issues_list, jira)
    dump_to_csv(populated_list)


if __name__ == "__main__":
    main()
