from jira import JIRA
import json
from configparser import ConfigParser

def populate_settings_from_config(config_file_name):
    configur = ConfigParser()
    configFilePath = config_file_name
    configur.read(configFilePath,encoding='UTF-8') 
    login =  configur.get('creds','email')
    passw =  configur.get('creds','passw')
    server = configur.get('settings','server')
    rest_api_version = int(configur.get('settings','rest_api_version'))
    expand = configur.get('settings','expand') 
    jql_query = configur.get('settings','jql')
    jira_options = {'settings': {'server': server,'rest_api_version': rest_api_version, 'expand':expand},'creds':{'login':login,'passw':passw},'jql':jql_query}
    sql_options = configur.get('creds','sql_conn')
    return jira_options,sql_options

# gets issue object via jira API, saves into a json
#NO_TEST
def get_jira_data(issue_key, jira_instance):
    issueobj = jira_instance.issue(issue_key, expand='changelog')
    issuestr = json.dumps(issueobj.raw,default=vars)     
    return issuestr


def save_data_json(issues_list,jira,str_control):
    if str_control == '1':
        issue = issues_list[0]
        json_string = get_jira_data(issue.key, jira)  
    else:
        json_array = []
        for issue in issues_list:
            json_array.append(get_jira_data(issue.key, jira))
            print(f'processed {issue.key}')
        print(f'processed total of {len(json_array)} issues')
        json_string = json.dumps(json_array)     
    return json_string    