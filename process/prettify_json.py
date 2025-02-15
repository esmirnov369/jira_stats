# gets issue obj
def get_field_value(issue, field_path, default="N/A"):
    """Helper function to safely get a value from a nested dictionary."""
    keys = field_path.split('.')
    value = issue
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    return value


def populate_jira_from_json(issue):
    summary = get_field_value(issue, "fields.summary")
    issue_type = get_field_value(issue, "fields.issuetype.name")
    parent = get_field_value(issue, "fields.parent.key") if issue_type in (
        "Acceptance bug", "Design sub-task", "Sub-task") else None
    issue_key = issue["key"]
    implementer = get_field_value(
        issue, "fields.customfield_10502.displayName", "N/A")
    team = get_field_value(issue, "fields.customfield_156807.value")
    product = get_field_value(issue, "fields.customfield_177900.value")
    planned_start = get_field_value(issue, "fields.customfield_10100")
    planned_end = get_field_value(issue, "fields.customfield_10101")
    priority = get_field_value(issue, "fields.priority.name")
    reason = get_field_value(issue, "fields.customfield_158100", "value")
    project = get_field_value(issue, "fields.project.key")
    issue_size = get_field_value(issue, "fields.customfield_169100.value")
    epic_name = get_field_value(issue, "fields.customfield_11914")

    transact_list = [
        {"to": "New", "from": "void", "time_stamp": issue["fields"]["created"]}
    ]

    for history in issue["changelog"]["histories"]:
        for item in history["items"]:
            if item["field"] == "status":
                transact_list.append({
                    "time_stamp": history["created"],
                    "from": item["fromString"],
                    "to": item["toString"]
                })
                break  # No need to check other items in the same history

    metadata = {
        "issue_size": issue_size,
        "issue_key": issue_key,
        "summary": summary,
        "issue_type": issue_type,
        "implementer": implementer,
        "team": team,
        "parent": parent,
        "project": project,
        "epic_name": epic_name,
        "reason": reason,
        "priority": priority,
        "PlannedStart": planned_start,
        "PlannedEnd": planned_end,
        "Product": product
    }

    return {"metadata": metadata, "history": transact_list}
