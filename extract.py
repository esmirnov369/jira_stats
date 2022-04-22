from jira import JIRA
import creds
import json
import jsons


# gets one issue by key, parses transitions, calls time calc function
#no test
def get_jira_data(issue_key, jira_instance):
    issueobj = jira_instance.issue(issue_key, expand='changelog')
    issuestr = json.dumps(issueobj.raw,default=vars)     
    return issuestr

#gets json string, parses into data structures
#need test
def populate_jira_from_json(json_string):
    issue = json.loads(json_string)
    summary = issue["fields"]["summary"]
    issue_type = issue["fields"]["issuetype"]["name"]
    if issue_type in ('Acceptance bug','Design sub-task'):
        parent = issue["fields"]["parent"]["key"]
    else:
        parent = None    
    issue_key = issue["key"]
    implementer = issue["fields"]["customfield_10502"]["displayName"] if issue["fields"]["customfield_10502"] else "N/A"
    fix_version = issue["fields"]["fixVersions"][0]["name"] if issue["fields"]["fixVersions"] else "N/A"
    team = issue["fields"]["customfield_156807"]["value"] 
    try:
        issue_size = issue["fields"]["customfield_169100"]["value"] 
    except:
        issue_size = "NA"
    transact_list = []
    transact_list.append({'to': 'CREATION', 'from': 'void',
                         'time_stamp': issue["fields"]["created"]})

    for history in issue["changelog"]["histories"]:
        change_dict = {}
        change_dict['to'] = ''
        change_dict['from'] = ''
        for item in history["items"]:
            if item["field"] == "status":
                change_dict['time_stamp'] = history["created"]
                change_dict['from'] = (item["fromString"])  # new value
                change_dict['to'] = (item["toString"])  # new value
                transact_list.append(change_dict)
    metadata = {'issue_size': issue_size, 'fix_version': fix_version,  'issue_key': issue_key,
                  'summary': summary, 'issue_type': issue_type, 'implementer': implementer, 'team':team, 'parent': parent }
    issue_dict = {}
    issue_dict['metadata'] = metadata
    issue_dict['history'] = transact_list
    print(f'finished processing {issue_key}')
    return issue_dict


def main():
    '''it's main'''
    jira_options = creds.options
    login = creds.email
    passw = creds.passw
    jira = JIRA(options=jira_options, basic_auth=(login, passw))
    try:
        jql_query = creds.jql
        issues_list = jira.search_issues(jql_query, maxResults=400)
    except:
        print('JQL or Auth error')
        return
    data_list = []    

    mock_data = jira.search_issues(jql_query, maxResults=1)
    for issue in mock_data:
        mock_obj = get_jira_data(issue.key, jira)
    with open('mock_raw.json', 'w') as outfile:
        outfile.write(mock_obj)


    for issue in issues_list:
        json_obj = get_jira_data(issue.key, jira)
        data_list.append(populate_jira_from_json(json_obj))
    
    json_string = json.dumps(data_list)     
    with open('json_data.json', 'w') as outfile:
        outfile.write(json_string)

if __name__ == "__main__":
    main()
