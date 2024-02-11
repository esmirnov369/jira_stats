import json
from dateutil.parser import parse
from importlib_metadata import metadata
import pandas as pd
import numpy as np
from datetime import datetime, timezone

SECONDS_IN_HOUR = 3600


class JiraIssue:
    """jira ticket instance that has some descriptive fields,
    an extract of history and a data_dict
    """

    def __init__(self, metadata, history):
        self.issue_key = metadata["issue_key"]
        self.summary = metadata["summary"]
        self.issue_type = metadata["issue_type"]
        self.implementer = metadata["implementer"]
        self.fix_version = metadata["fix_version"]
        self.issue_size = metadata["issue_size"]
        self.team = metadata["team"]
        self.parent = metadata["parent"]
        self.project = metadata["project"]
        self.components = metadata["components"]
        self.priority = metadata["priority"]

        self.history = history
        self.data_dict = metadata

    def calc_time(self):
        print(f"processing {self.issue_key}")
        """iterate thru a list of status change events and calc time
        populates a data_dict member of the instance with time for each stat"""
        statuses = set()
        if len(self.history) > 1:
            self.history[0]["to"] = self.history[1]["from"]
        self.data_dict["ready_time"] = None
        self.data_dict["released_time"] = None
        for val in self.history:
            status = val["to"]
            statuses.add(status)
            self.data_dict[status] = 0
        for index, val in enumerate(self.history):
            if val["from"] == "void":
                created_stamp = val["time_stamp"]
                self.data_dict["created_time"] = created_stamp
                self.data_dict["lifetime"] = (
                    datetime.now(timezone.utc) - parse(created_stamp)
                ).total_seconds()
                self.data_dict["lifetime"] = round(
                    (self.data_dict["lifetime"] / SECONDS_IN_HOUR), 2
                )
            else:
                if val["to"] in ("Ready", "Done", "Acknowledged"):
                    self.data_dict["ready_time"] = val["time_stamp"]
                status_name = val["from"]
                if val["to"] in ("Released"):
                    self.data_dict["released_time"] = val["time_stamp"]
                time_event = parse(val["time_stamp"])
                time_prev = parse(self.history[index - 1]["time_stamp"])
                self.data_dict[status_name] = (
                    self.data_dict[status_name]
                    + (time_event - time_prev).total_seconds()
                )
        self.data_dict["created_time"] = parse_date(self.data_dict["created_time"])
        if self.data_dict["ready_time"] != None:
            self.data_dict["ready_time"] = parse_date(self.data_dict["ready_time"])
        if self.data_dict["released_time"] != None:
            self.data_dict["released_time"] = parse_date(
                self.data_dict["released_time"]
            )
        for val in statuses:
            if self.data_dict[val] > 0:
                self.data_dict[val] = round((self.data_dict[val] / SECONDS_IN_HOUR), 2)
        last_status = self.history[len(self.history) - 1]["to"]
        self.data_dict["last_status"] = last_status
        last_transition_time = parse(self.history[len(self.history) - 1]["time_stamp"])
        time_diff = (datetime.now(timezone.utc) - last_transition_time).total_seconds()
        time_diff = round((time_diff / SECONDS_IN_HOUR), 2)
        self.data_dict[last_status] = time_diff

    def __repr__(self):
        return f"{self.data_dict}"


def parse_date(date, fmt=None):
    """
    converts data from a long timestamp to a better one
    """
    if fmt is None:
        fmt = "%Y-%m-%d %H:%M:%S"
    get_date_obj = parse(str(date))
    return str(get_date_obj.strftime(fmt))


def dataframe_manipulations(issues_list, folder, filename):
    """
    iterate over issues list and append them one by one to a dataframe, save
    data frame on the drive
    """
    df = pd.DataFrame.from_dict([issues_list[0].data_dict])

    for issue in issues_list:
        sub_df = pd.DataFrame.from_dict([issue.data_dict])
        df = pd.concat([sub_df, df], axis=0)

    df["created_time"] = pd.to_datetime(df["created_time"])
    df["ready_time"].loc[df["ready_time"].notnull()] = pd.to_datetime(
        df["ready_time"].loc[df["ready_time"].notnull()]
    )
    bugs_df = df.loc[df["issue_type"].isin(["Acceptance bug", "Design sub-task"])]
    bugs_df = bugs_df.groupby(by="parent").size()
    combo = pd.merge(
        df,
        bugs_df.rename("defects"),
        how="left",
        left_on=["issue_key"],
        right_on=["parent"],
    )
    accept_array = combo[combo["issue_type"].str.contains("Acceptance bug")]
    accept_array = accept_array.groupby(["parent"])["parent"].count()
    des_array = combo[combo["issue_type"].str.contains("Design sub-task")]
    des_array = des_array.groupby(["parent"])["parent"].count()
    defects_array = pd.DataFrame(
        dict(n_accept=accept_array, n_design=des_array)
    ).reset_index()
    defects_array = defects_array.fillna(0)
    defects_array.rename(columns={"parent": "merge_key"}, inplace=True)
    combo = pd.merge(
        combo, defects_array, how="left", left_on=["issue_key"], right_on=["merge_key"]
    )
    combo = combo.drop(["merge_key"], axis=1)

    return combo


def save_df_to_csv(df, folder, output_name):
    df.to_csv(folder + "/" + output_name + ".csv", index=False, encoding="utf-8")


def calc_cycle_time(df, setup="agnostic"):
    if setup == "API":
        collist = [
            "Planned",
            "Specification Review",
            "ToDo",
            "Ready to Develop",
            "In Progress",
            "Review",
            "Resolved",
            "Testing",
            "Ready",
        ]
        for col in collist:
            if col not in df.columns:
                df[col] = 0
        df["cycle_hours_api"] = df.query("project == 'API'")[collist].sum(axis=1)
        df["cycle_days_api"] = df["cycle_hours_api"] / 24  # 24 hours in a day
    else:
        df = df
    return df


def push_df_to_sql(dataframe, connection):
    dataframe.to_sql("TABLE", con=connection, if_exists="replace")
    return
