#!/usr/bin/env python3
"""Build a signed-importable Apple Shortcut plist for coach metrics."""

import os
import plistlib
import uuid


OBJ = "\ufffc"


def token_string(parts):
    text = ""
    attachments = {}
    for part in parts:
        if isinstance(part, str):
            text += part
            continue
        start = len(text)
        text += OBJ
        attachments[f"{{{start}, 1}}"] = part
    return {
        "Value": {
            "string": text,
            "attachmentsByRange": attachments,
        },
        "WFSerializationType": "WFTextTokenString",
    }


def output_ref(action_uuid, output_name):
    return {
        "Type": "ActionOutput",
        "OutputUUID": action_uuid,
        "OutputName": output_name,
    }


def action(identifier, params=None):
    params = dict(params or {})
    params.setdefault("UUID", str(uuid.uuid4()).upper())
    return {
        "WFWorkflowActionIdentifier": identifier,
        "WFWorkflowActionParameters": params,
    }


def ask(prompt):
    return action(
        "is.workflow.actions.ask",
        {
            "WFAskActionPrompt": prompt,
            "WFInputType": "Number",
        },
    )


def main():
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shortcuts")
    os.makedirs(out_dir, exist_ok=True)

    date = action("is.workflow.actions.date", {"WFDateActionMode": "Current Date"})
    formatted_date = action(
        "is.workflow.actions.format.date",
        {
            "WFDateFormatStyle": "Custom",
            "WFTimeFormatStyle": "None",
            "WFDateFormat": "yyyy-MM-dd",
        },
    )
    duration = ask("Total duration minutes?")
    active_kcal = ask("Total active calories?")
    avg_hr = ask("Average heart rate?")
    peak_hr = ask("Peak heart rate?")
    hr_stop = ask("Heart rate at stop?")
    hr_1min = ask("Heart rate 1 minute after stop?")

    text = action(
        "is.workflow.actions.gettext",
        {
            "WFTextActionText": token_string(
                [
                    "Apple Health metrics\n",
                    "date: ",
                    output_ref(formatted_date["WFWorkflowActionParameters"]["UUID"], "Formatted Date"),
                    "\n",
                    "total_duration_min: ",
                    output_ref(duration["WFWorkflowActionParameters"]["UUID"], "Ask for Input"),
                    "\n",
                    "total_active_kcal: ",
                    output_ref(active_kcal["WFWorkflowActionParameters"]["UUID"], "Ask for Input"),
                    "\n",
                    "avg_hr: ",
                    output_ref(avg_hr["WFWorkflowActionParameters"]["UUID"], "Ask for Input"),
                    "\n",
                    "peak_hr: ",
                    output_ref(peak_hr["WFWorkflowActionParameters"]["UUID"], "Ask for Input"),
                    "\n",
                    "hr_at_stop: ",
                    output_ref(hr_stop["WFWorkflowActionParameters"]["UUID"], "Ask for Input"),
                    "\n",
                    "hr_1min_post: ",
                    output_ref(hr_1min["WFWorkflowActionParameters"]["UUID"], "Ask for Input"),
                    "\n",
                ]
            )
        },
    )
    show = action(
        "is.workflow.actions.showresult",
        {
            "Text": token_string(
                [output_ref(text["WFWorkflowActionParameters"]["UUID"], "Text")]
            )
        },
    )

    shortcut = {
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowClientVersion": "2700.0.4",
        "WFWorkflowName": "Coach Metrics Paste",
        "WFWorkflowIcon": {
            "WFWorkflowIconStartColor": 463140863,
            "WFWorkflowIconGlyphNumber": 59780,
        },
        "WFWorkflowImportQuestions": [],
        "WFWorkflowInputContentItemClasses": [],
        "WFWorkflowOutputContentItemClasses": ["NSString"],
        "WFWorkflowHasOutputFallback": False,
        "WFWorkflowTypes": [],
        "WFWorkflowActions": [
            date,
            formatted_date,
            duration,
            active_kcal,
            avg_hr,
            peak_hr,
            hr_stop,
            hr_1min,
            text,
            show,
        ],
    }

    raw_path = os.path.join(out_dir, "Coach Metrics Paste.unsigned.shortcut")
    with open(raw_path, "wb") as fh:
        plistlib.dump(shortcut, fh, fmt=plistlib.FMT_BINARY, sort_keys=False)
    print(raw_path)


if __name__ == "__main__":
    main()
