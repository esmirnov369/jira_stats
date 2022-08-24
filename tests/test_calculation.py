import unittest
import process
import pandas as pd
import json
import os


class Test_Config(unittest.TestCase):
    def test_config_reader(self):
        optionset =  process.populate_settings_from_config(os.getcwd() + '\\data\\config.ini')
        self.jira_options = optionset[0]
        self.assertTrue(len(self.jira_options)==3)       

class TestIssue(unittest.TestCase):
    metadata = {'issue_size': 'XS', 
                'fix_version': 'N/A', 
                'issue_key': 'API-12345',
                'summary': 'Implement Something',
                'issue_type': 'Engineering Task',
                'implementer': 'First Name Last Name',
                'team':'API',
                'project': 'API', 
                'parent': '0'}
    history = [ {'to': 'New', 'from': 'void', 'time_stamp': '2022-01-02T10:26:06.319+0300'}, 
                {'to': 'Specification', 'from': 'New', 'time_stamp': '2022-04-08T10:31:45.398+0300'},
                {'to': 'Specification Review', 'from': 'Specification', 'time_stamp': '2022-04-08T11:31:50.180+0300'},
                {'to': 'Planned', 'from': 'Specification Review', 'time_stamp': '2022-04-08T12:20:54.770+0300'},
                {'to': 'Specification Review', 'from': 'Planned', 'time_stamp': '2022-04-08T12:21:56.908+0300'},
                {'to': 'ToDo', 'from': 'Specification Review', 'time_stamp': '2022-04-08T14:32:01.864+0300'}, 
                {'to': 'Ready to Develop', 'from': 'ToDo', 'time_stamp': '2022-04-08T15:32:05.647+0300'}, 
                {'to': 'In Progress', 'from': 'Ready to Develop', 'time_stamp': '2022-04-08T16:32:11.820+0300'},
                {'to': 'Review', 'from': 'In Progress', 'time_stamp': '2022-04-08T17:19:30.117+0300'}, 
                {'to': 'Ready', 'from': 'Review', 'time_stamp': '2022-04-08T20:19:35.219+0300'}]

   
    #open a raw json file, try to populate a dict from it, exepect it to happen without issues
    def test_populate_jira_from_json(self):
        with open('reporting/mock_raw.json') as json_file:
            data_str = json.load(json_file)
        data_raw = json.dumps(data_str)            
        self.issue_dict = process.populate_jira_from_json(data_raw)    
        self.assertTrue(type(self.issue_dict) == dict)
        self.assertTrue(len(self.issue_dict)>0)
        self.assertTrue(len(self.issue_dict["metadata"]["issue_key"])>0)

    #test how JiraIssue works from a poorly created mock
    def test_create_issue(self, metadata=metadata, history=history):
        mock_issue = process.JiraIssue(metadata, history)
        self.assertTrue(len(mock_issue.history) > 0)

    #try to calculate time values based on mock's preset transitions
    def test_calc_time(self, metadata=metadata, history=history):
        mock_issue = process.JiraIssue(metadata, history)
        mock_issue.calc_time()
        self.assertEqual(mock_issue.data_dict['New'], 2304.09)
        self.assertEqual(mock_issue.data_dict['Specification'], 1.0)
        self.assertEqual(mock_issue.data_dict['Specification Review'], 2.99)
        self.assertEqual(mock_issue.data_dict['Planned'], 0.02)
        self.assertEqual(mock_issue.data_dict['ToDo'], 1.0)
        self.assertEqual(mock_issue.data_dict['Ready to Develop'], 1.0)
        self.assertEqual(mock_issue.data_dict['In Progress'], 0.79)
        self.assertEqual(mock_issue.data_dict['Review'], 3.0)
        self.assertEqual(mock_issue.data_dict['Ready'], 0.0)
        pass

    #assert that we can create a data frame based on a jira issue
    def test_create_data(self, metadata=metadata, history=history):
        df = pd.DataFrame()
        mock_issue = process.JiraIssue(metadata, history)
        issues_list = [mock_issue]
        for issue in issues_list:
            issue.calc_time()
            df = df.append(issue.data_dict, ignore_index=True)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.empty, False)
        self.assertEqual(df.ndim, 2)
        self.assertEqual(df.shape, (1, 20))
        self.assertEqual(df.size, 20)
        pass


if __name__ == '__main__':
    unittest.main()
