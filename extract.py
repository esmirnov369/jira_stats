from jira import JIRA
import creds
import json

# gets issue object via jira API, saves into a json
#no test
def get_jira_data(issue_key, jira_instance):
    issueobj = jira_instance.issue(issue_key, expand='changelog')
    issuestr = json.dumps(issueobj.raw,default=vars)     
    return issuestr

#connects to jira via creds, gets jira fields into a json, saves a jsonified list of field data on drive (raw)
#also populates a mock json for unittests
def main():
    '''it's main'''
    jira_options = creds.options
    login = creds.email
    passw = creds.passw
    jira = JIRA(options=jira_options, basic_auth=(login, passw))
    try:
        jql_query = creds.jql
        issues_list = jira.search_issues(jql_query, maxResults=2000)
    except:
        print('JQL or Auth error')
        return

    mock_data = jira.search_issues(jql_query, maxResults=1)
    for issue in mock_data:
        mock_obj = get_jira_data(issue.key, jira)
    with open('mock_raw.json', 'w') as outfile:
        outfile.write(mock_obj)

    json_array = []
    for issue in issues_list:
        json_array.append(get_jira_data(issue.key, jira))
        print(f'processed {issue.key}')
    print(f'processed total of {len(json_array)} issues')
    json_string = json.dumps(json_array)     
    with open('raw_jsondata.json', 'w') as outfile:
        outfile.write(json_string)

if __name__ == "__main__":
    main()
