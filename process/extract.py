from jira import JIRA
import json
from configparser import ConfigParser
from datetime import date
import time


def populate_settings_from_config(config_file_name):
    configur = ConfigParser()
    configFilePath = config_file_name
    configur.read(configFilePath,encoding='UTF-8') 
    login =  configur.get('creds','email')
    passw =  configur.get('creds','passw')
    server = configur.get('settings','server')
    runtype = configur.get('settings','runtype')
    rest_api_version = int(configur.get('settings','rest_api_version'))
    expand = configur.get('settings','expand') 
    jql_query = configur.get('settings','jql')
    jira_options = {'settings': {'server': server,'rest_api_version': rest_api_version, 'expand':expand},'creds':{'login':login,'passw':passw},'jql':jql_query, 'runtype':runtype}
    sql_options = configur.get('creds','sql_conn')
    data_object = {'jira_options': jira_options, 'sql_options': sql_options}
    return data_object


