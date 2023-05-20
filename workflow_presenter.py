import  process
import os
import json
import dictdiffer  

def main():
    
    #read config
    option_set = process.populate_settings_from_config(os.getcwd() + '\\data\\config.ini')
    jira_options = option_set['jira_options']
    sql_options = option_set['sql_options']
    #create a jira connection instance
    #run query thru connection
    print("connecting to JIRA")
    jira = process.JIRA(options=jira_options['settings'], basic_auth=(jira_options['creds']['login'], jira_options['creds']['passw']))
    projects = ['MBIOS','MBAND','API'] 
    for project in projects:
        proj_instance = jira.issue_types_for_project(project)
        issue_dict = {}
        for i_type in range(0,len(proj_instance)):
            status_collection = []
            for i_status in proj_instance[i_type].statuses:
                status_collection.append(i_status.name)
            issue_dict[proj_instance[i_type].name] = status_collection
        filename = 'Reporting/' + project + 'trial.json'
        try:
            with open(filename) as json_file:
                old_data = json.load(json_file)
            diff = list(dictdiffer.diff(issue_dict, old_data))
            if len(diff)>0:
                for change in diff:         
                    print(f'change in {project} detected', change)
            else:
                print(f'all ok with {project}')            
        except:
            print('Data missing!')
      

        with open(filename, "w") as write_file:
            json.dump(issue_dict, write_file, indent=4)
    
   
  
   
   

if __name__ == "__main__":
    main()
