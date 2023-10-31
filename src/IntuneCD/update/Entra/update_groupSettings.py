#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module is used to update all Group Settings in Entra.
"""

import glob
import json

from deepdiff import DeepDiff

from ...intunecdlib.check_file import check_file
from ...intunecdlib.diff_summary import DiffSummary
from ...intunecdlib.graph_request import makeapirequest, makeapirequestPatch
from ...intunecdlib.load_file import load_file

# Set MS Graph endpoint
BASE_ENDPOINT = "https://graph.microsoft.com/v1.0/groupSettings"


def update(path, token, report):
    """
    This function updates all Group Settings in Entra if the configuration in Entra differs from the JSON/YAML file.

    :param path: Path to where the backup is saved
    :param token: Token to use for authenticating the request
    """

    diff_summary = []
    # Set Group Settings path
    configpath = path + "/Entra/Group Settings/" + "group_settings.*"

    file = glob.glob(configpath)
    # If group settings path exists, continue
    if file:
        # get all Group Settings
        entra_data = makeapirequest(BASE_ENDPOINT, token)

        file = check_file(path + "/Entra/Group Settings/", file[0].split("/")[-1])
        if file is False:
            return diff_summary
        # Check which format the file is saved as then open file, load data
        # and set query parameter
        with open(file, encoding="utf-8") as f:
            repo_data = load_file(file, f)

        if entra_data.get("value"):
            print("-" * 90)
            for repo_setting, group_setting in zip(
                repo_data["value"], entra_data["value"]
            ):
                if group_setting["id"] == repo_setting["id"]:
                    diff = DeepDiff(
                        group_setting["values"],
                        repo_setting["values"],
                        ignore_order=True,
                    ).get("values_changed", {})

                    # If any changed values are found, push them to Entra
                    if diff and report is False:
                        request_data = json.dumps(repo_setting)
                        makeapirequestPatch(
                            BASE_ENDPOINT + "/" + repo_setting["id"],
                            token,
                            q_param=None,
                            jdata=request_data,
                            status_code=204,
                        )

                    diff_config = DiffSummary(
                        data=diff,
                        name=repo_setting["displayName"],
                        type="Group Settings",
                    )

                    diff_summary.append(diff_config)

    return diff_summary
