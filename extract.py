from jira import JIRA
import json
from configparser import ConfigParser

#TODO write tests for a) reading config b) connecting to JIRA instance
def populate_settings_from_config(config_file_name):
    configur = ConfigParser()
    configFilePath = config_file_name
    configur.read(configFilePath) 
    login =  configur.get('creds','email')
    passw =  configur.get('creds','passw')
    server = configur.get('settings','server')
    rest_api_version = int(configur.get('settings','rest_api_version'))
    expand = configur.get('settings','expand') 
    jql_query = configur.get('settings','jql')
    jira_options = {'settings': {'server': server,'rest_api_version': rest_api_version, 'expand':expand},'creds':{'login':login,'passw':passw},'jql':jql_query}
    return jira_options

# gets issue object via jira API, saves into a json
#NO_TEST
def get_jira_data(issue_key, jira_instance):
    issueobj = jira_instance.issue(issue_key, expand='changelog')
    issuestr = json.dumps(issueobj.raw,default=vars)     
    return issuestr

#connects to jira via creds, gets jira fields into a json, saves a jsonified list of field data on drive (raw)
#also populates a mock json for unittests
def main():
    '''it's main'''
    jira_options = populate_settings_from_config('config.ini')
    settings = jira_options['settings']
    creds = jira_options['creds']
    jql = jira_options['jql']
    jira = JIRA(options=settings, basic_auth=(creds['login'], creds['passw']))
    try:
        issues_list = jira.search_issues(jql, maxResults=1500)
    except:
        print('JQL or Auth error')
        return

    #create a mock json for unit tests with just one issue downloaded
    mock_data = jira.search_issues(jql, maxResults=1)
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
