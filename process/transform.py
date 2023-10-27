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


def calc_cycle_time(df, setup="MB"):
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


def parse_epics_MB(df, setup="API"):
    if setup == "MB":
        epic_dict = {
            "MBAND-62602": "Редизайн НС",
            "MBAND-62597": "Редизайн НС",
            "MBAND-74141": "Редизайн НС",
            "MBAND-62649": "Редизайн НС",
            "MBAND-62607": "Редизайн НС",
            "MBAND-33762": "Редизайн деталей счета",
            "MBAND-39913": "Кэшбэки в плашке бонусов на дебетовом и кредитном счете",
            "MBAND-29961": "Кубышка",
            "MBAND-31394": "Драг энд дроп на главной",
            "MBAND-38257": "Печать карты",
            "MBAND-40511": "Удаление информации о Google Pay",
            "MBAND-41467": "Редизайн деталей счета. Вклад. Запуск на сотрудниках",
            "MBAND-35168": "Выбор дизайна карты для Apple/Google Pay",
            "MBAND-41158": "Редизайн перевыпуска карты",
            "MBAND-42910": "Редизайн тарифных лимитов",
            "MBAND-43976": "[Самозанятость] Итерация 2",
            "MBAND-46480": "Доработки старых вкладов в юанях (до редизайна)",
            "MBAND-47922": "Редизайн перевыпуска карты - часть 2",
            "MBAND-48960": "Кубышка. Отказ от овердрафта",
            "MBAND-50083": "Кубышка. Преколлекшен и коллекшен",
            "MBAND-56840": "Редизайн деталей счета. Вклад. ч. 2 - Доработки",
            "MBAND-52254": "Виртуальные карты. Не отображать иконку облака",
            "MBAND-62595": "Редизайн НС",
            "MBAND-56091": "Золотой счет. Новый продукт. Запуск на сотрудниках",
            "MBAND-52805": "Оптимизация экранов счетов и карт под новый флоу шаринга",
            "MBAND-63508": "Кубышка. Отображение любого количества дней грейса",
            "MBAND-60780": "Хранение слитков. Новый продукт",
            "MBAND-68081": "Кубышка. Улучшение описания о работе и комиссии",
            "MBAND-68301": "Редизайн НС",
            "MBAND-72704": "Золотой счет. Доработки для технического запуска",
            "MBAND-69651": "Платежный стикер. Доработка отображения",
            "MBAND-70585": "Переезд на TUI-компоненты: Главная МБ",
            "MBAND-71818": "Виртуальная карта. Доработка отображения, точки входа для допечати",
            "MBAND-73734": "Кнопка Пополнить",
            "MBAND-72973": "Самозанятость. Инвалидация id подписки на налоговые уведомления",
            "MBIOS-59042": "Редизайн НС",
            "MBIOS-59040": "Редизайн НС",
            "MBIOS-59038": "Редизайн НС",
            "MBIOS-59077": "Редизайн НС",
            "MBIOS-38878": "Кэшбэки в плашке бонусов на дебетовом и кредитном счете",
            "MBIOS-30789": "Кубышка (займ до зарплаты)",
            "MBIOS-37524": "Печать карты",
            "MBIOS-32019": "Драг энд дроп на главной",
            "MBIOS-39422": "Удаление информации о Apple Pay",
            "MBIOS-40221": "Редизайн деталей счета. Вклад. Запуск на сотрудниках",
            "MBIOS-39977": "Редизайн перевыпуска карты",
            "MBIOS-35018": "Выбор дизайна карты для Apple/Google Pay",
            "MBIOS-41365": "Редизайн тарифных лимитов",
            "MBIOS-42302": "[Самозанятость] Итерация 2",
            "MBIOS-44467": "Доработки старых вкладов в юанях (до редизайна)",
            "MBIOS-46596": "Бизнес-залы Every Loung",
            "MBIOS-46807": "Кубышка. Отказ от овердрафта",
            "MBIOS-51871": "Редизайн деталей счета. Вклад. Часть 2. Аналитика, диплинки, дизайн улучшения",
            "MBIOS-47660": "Кубышка. Преколлекшен и коллекшен",
            "MBIOS-51873": "Редизайн деталей счета. Экран График вклада",
            "MBIOS-49852": "Виртуальные карты. Не отображать иконку облака",
            "MBIOS-50289": "Оптимизация экранов счетов и карт под новый флоу шаринга",
            "MBIOS-59035": "Редизайн НС",
            "MBIOS-53960": "Редизайн деталей счета. Вклад. ч. 3 - Доработки",
            "MBIOS-53363": "Золотой счет. Новый продукт. Запуск на сотрудниках",
            "MBIOS-59970": "Кубышка. Отображение любого количества дней грейса",
            "MBIOS-57385": "Хранение слитков. Новый продукт",
            "MBIOS-68038": "Редизайн НС",
            "MBIOS-64229": "Кубышка. Улучшение описания о работе и комиссии",
            "MBIOS-64463": "Редизайн НС",
            "MBIOS-56607": "Добавление и отображение счетов Сбера. Технический запуск",
            "MBIOS-65666": "Платежный стикер. Доработка отображения",
            "MBIOS-67405": "Виртуальная карта. Доработка отображения, точки входа для допечати",
        }
        for key in epic_dict:
            df.loc[df["epic_name"] == key, "feature_name"] = epic_dict[key]

    return df


def push_df_to_sql(dataframe, connection):
    dataframe.to_sql("TABLE", con=connection, if_exists="replace")
    return
