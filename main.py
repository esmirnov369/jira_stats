import process
import os
import json
from datetime import datetime


def main():
    # read config
    option_set = process.populate_settings_from_config(
        os.getcwd() + "\\data\\config.ini"
    )
    jira_options = option_set["jira_options"]
    sql_options = option_set["sql_options"]

    # create a jira connection instance
    # run query thru connection
    jql_success = True

    if jql_success != False:
        print("connecting to JIRA")
        try:
            jira = process.JIRA(
                options=jira_options["settings"],
                basic_auth=(
                    jira_options["creds"]["login"],
                    jira_options["creds"]["passw"],
                ),
            )
            issues_list = jira.search_issues(
                jira_options["jql"],
                expand="changelog",
                maxResults=1000,
                json_result=True,
            )
            jql_success = True
        except:
            print("JQL or Auth error")
            jql_success = False

    # save raw json dump
    if jql_success:
        print("dumping jsons")

        with open("reporting/json_dump.json", "w") as fp:
            json.dump(issues_list, fp)

    print("reading json")
    with open("reporting/json_dump.json") as json_file:
        data = json.load(json_file)

    # prettyfy json
    pretty_list = []
    for issue in data["issues"]:
        pretty_list.append(process.populate_jira_from_json(issue))
    json_string = json.dumps(pretty_list)
    with open("reporting/json_pretty.json", "w") as outfile:
        outfile.write(json_string)
    print(f"prettified and saved {len(pretty_list)} issues")

    with open("reporting/json_pretty.json") as json_file:
        data = json.load(json_file)
    issue_list = []
    for list_item in data:
        metadata = list_item["metadata"]
        history = list_item["history"]
        issue = process.JiraIssue(metadata, history)
        issue.calc_time()
        issue_list.append(issue)
    df = process.dataframe_manipulations(issue_list, "reporting", "Ops")
    df = process.calc_cycle_time(df)
    process.save_df_to_csv(df, "reporting", "cycle")
    return


if __name__ == "__main__":
    main()
