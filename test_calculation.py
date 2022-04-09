import unittest
from main import JiraIssue
import pandas as pd


class TestIssue(unittest.TestCase):
    metadata = {'issueSize': 'XS', 'fixVersion': 'N/A', 'issue_key': 'API-12345',
                'summary': 'Implement Something', 'issuetype': 'Engineering Task', 'implementer': 'First Name Last Name'}
    history = [{'to': 'CREATION', 'from': 'void', 'time_stamp': '2022-04-02T10:26:06.319+0300'}, {'to': 'Specification', 'from': 'New', 'time_stamp': '2022-04-08T10:31:45.398+0300'}, {'to': 'Specification Review', 'from': 'Specification', 'time_stamp': '2022-04-08T10:31:50.180+0300'}, {'to': 'Planned', 'from': 'Specification Review', 'time_stamp': '2022-04-08T10:31:54.770+0300'}, {'to': 'Specification Review', 'from': 'Planned', 'time_stamp': '2022-04-08T10:31:56.908+0300'},
               {'to': 'ToDo', 'from': 'Specification Review', 'time_stamp': '2022-04-08T10:32:01.864+0300'}, {'to': 'Ready to Develop', 'from': 'ToDo', 'time_stamp': '2022-04-08T10:32:05.647+0300'}, {'to': 'In Progress', 'from': 'Ready to Develop', 'time_stamp': '2022-04-08T10:32:11.820+0300'}, {'to': 'Review', 'from': 'In Progress', 'time_stamp': '2022-04-08T12:19:30.117+0300'}, {'to': 'Ready', 'from': 'Review', 'time_stamp': '2022-04-08T12:19:35.219+0300'}]

    def test_create_issue(self, metadata=metadata, history=history):
        mock_issue = JiraIssue(metadata, history, 0, [])
        self.assertTrue(len(mock_issue.history) > 0)

    def test_calculate_time(self, metadata=metadata, history=history):
        mock_issue = JiraIssue(metadata, history, 0, [])
        mock_issue.calc_time()
        self.assertEqual(mock_issue.data_dict['New'], 144.09)
        self.assertEqual(mock_issue.data_dict['Specification'], 0.0)
        self.assertEqual(mock_issue.data_dict['Specification Review'], 0.0)
        self.assertEqual(mock_issue.data_dict['Specification Review'], 0.0)
        self.assertEqual(mock_issue.data_dict['Planned'], 0.0)
        self.assertEqual(mock_issue.data_dict['ToDo'], 0.0)
        self.assertEqual(mock_issue.data_dict['Ready to Develop'], 0.0)
        self.assertEqual(mock_issue.data_dict['In Progress'], 1.79)
        self.assertEqual(mock_issue.data_dict['Review'], 0.0)
        self.assertEqual(mock_issue.data_dict['Ready'], 0.0)
        pass

    def test_create_data(self, metadata=metadata, history=history):
        df = pd.DataFrame()
        mock_issue = JiraIssue(metadata, history, 0, [])
        issues_list = [mock_issue]
        for issue in issues_list:
            print(f"starting on {issue.issue_key}")
            issue.calc_time()
            df = df.append(issue.data_dict, ignore_index=True)
            print(f"{issue.issue_key} is processed")
        self.assertEqual(len(df), 1)
        self.assertEqual(df.empty, False)
        self.assertEqual(df.ndim, 2)
        self.assertEqual(df.shape, (1, 17))
        self.assertEqual(df.size, 17)
        pass


if __name__ == '__main__':
    unittest.main()
