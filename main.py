import  process
import os
import json

def main():
    #read config
    option_set = process.populate_settings_from_config(os.getcwd() + '\\data\\config.ini')
    jira_options = option_set[0]
    sql_options = option_set[1]
    #create a jira connection instance
    #run query thru connection
    try:
        jira = process.JIRA(options=jira_options['settings'], basic_auth=(jira_options['creds']['login'], jira_options['creds']['passw']))
        issues_list = jira.search_issues(jira_options['jql'], maxResults=1555)
        jql_success = True
    except:
        print('JQL or Auth error')
        jql_success = False
        
    
    if jql_success:
        with open('reporting/mock_raw.json', 'w') as outfile:
            outfile.write(process.save_data_json(issues_list,jira,'1'))

        with open('reporting/json_dump.json', 'w') as outfile:
            outfile.write(process.save_data_json(issues_list,jira,'max'))


    with open('reporting/json_dump.json') as json_file:
        data = json.load(json_file)
   
    pretty_list = []
    for issue in data:
        pretty_list.append(process.populate_jira_from_json(issue))
    json_string = json.dumps(pretty_list)     
    with open('reporting/json_pretty.json', 'w') as outfile:
        outfile.write(json_string)
    print(f'prettified {len(pretty_list)} issues')

    with open('reporting/json_pretty.json') as json_file:
        data = json.load(json_file)        
    issue_list = []
    for list_item in data:
        metadata=list_item['metadata']
        history = list_item['history']
        issue = process.JiraIssue(metadata,history)
        issue.calc_time()
        issue_list.append(issue)
    df = process.dump_to_csv(issue_list,'reporting')

    process.push_postgres(df,'jira',sql_options)


if __name__ == "__main__":
    main()
