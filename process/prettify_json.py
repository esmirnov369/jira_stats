import json

#gets json string, parses into data structures
def populate_jira_from_json(json_string):
    issue = json.loads(json_string)
    summary = issue["fields"]["summary"]
    issue_type = issue["fields"]["issuetype"]["name"]
    if issue_type in ('Acceptance bug','Design sub-task','Sub-task'):
        parent = issue["fields"]["parent"]["key"]
    else:
        parent = None    
    issue_key = issue["key"]
    implementer = issue["fields"]["customfield_10502"]["displayName"] if issue["fields"]["customfield_10502"] else "N/A"
    fix_version = issue["fields"]["fixVersions"][0]["name"] if issue["fields"]["fixVersions"] else "N/A"
    try:
        team = issue["fields"]["customfield_156807"]["value"]
    except:
        team = 'N/A'
    priority = issue["fields"]["priority"]["name"]
    try:
        reason =  issue["fields"]["customfield_158100"][0]["value"]
    except:
        reason = 'N/A'              
    project = issue["fields"]["project"]["key"]
    try:
        issue_size = issue["fields"]["customfield_169100"]["value"] 
    except:
        issue_size = "NA"
    try:
        epic_name = issue["fields"]["customfield_11914"]
    except:
        epic_name = "NA"    
    transact_list = []
    transact_list.append({'to': 'New', 'from': 'void',
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
    metadata = {'issue_size': issue_size, 'fix_version': fix_version,  'issue_key': issue_key, 'summary': summary,
                 'issue_type': issue_type, 'implementer': implementer, 'team':team, 'parent': parent, 'project': project,
                 'epic_name': epic_name, 'reason': reason, 'priority': priority}
    issue_dict = {}
    issue_dict['metadata'] = metadata
    issue_dict['history'] = transact_list
    print(f'finished processing {issue_key}')
    return issue_dict
