#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module contains all functions for the documentation.
"""

import base64
import binascii
import glob
import json
import os
import platform
import re

import yaml


def html_table(headers, rows):
    """
    Generate an HTML table from headers and rows.
    :param headers: List of column headers
    :param rows: List of row lists
    :return: HTML table as a string
    """
    table = "<table>\n<thead><tr>"
    for h in headers:
        table += f"<th>{h}</th>"
    table += "</tr></thead>\n<tbody>\n"
    for row in rows:
        table += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>\n"
    table += "</tbody>\n</table>"
    return table


def md_file(outpath):
    """
    This function creates the markdown file.

    :param outpath: The path to save the Markdown document to
    """
    if not os.path.exists(f"{outpath}"):
        open(outpath, "w+", encoding="utf-8").close()
    else:
        open(outpath, "w", encoding="utf-8").close()


def write_table(data):
    """
    This function creates the HTML table.

    :param data: The data to be written to the table
    :return: The HTML table as a string
    """
    return html_table(["setting", "value"], data)


def escape_markdown(text):
    """
    This function escapes markdown characters.

    :param text: The text to be escaped
    :return: The escaped text
    """

    # Escape markdown characters
    parse = re.sub(r"([\_*\[\]()\{\}`>\#\+\-=|\.!])", r"\\\1", text)

    return parse


def assignment_table(data):
    """
    This function creates the HTML assignments table.

    :param data: The data to be written to the table
    :return: The HTML table as a string
    """

    def write_assignment_table(data, headers):
        return html_table(headers, data)

    table = ""
    if "assignments" in data:
        assignments = data["assignments"]
        assignment_list = []
        for assignment in assignments:
            headers = ["intent", "target", "filter type", "filter name"]
            target = ""
            intent = ""
            if (
                assignment["target"]["@odata.type"]
                == "#microsoft.graph.allDevicesAssignmentTarget"
            ):
                target = "All Devices"
                intent = "Include"
            if (
                assignment["target"]["@odata.type"]
                == "#microsoft.graph.allLicensedUsersAssignmentTarget"
            ):
                target = "All Users"
                intent = "Include"
            if "groupName" in assignment["target"]:
                target = assignment["target"]["groupName"]
            if "intent" in assignment and assignment["intent"] not in ["apply", ""]:
                intent = assignment["intent"]
            else:
                if (
                    assignment["target"]["@odata.type"]
                    == "#microsoft.graph.groupAssignmentTarget"
                ):
                    intent = "Include"
                if (
                    assignment["target"]["@odata.type"]
                    == "#microsoft.graph.exclusionGroupAssignmentTarget"
                ):
                    intent = "Exclude"
            assignment_list.append(
                [
                    intent,
                    target,
                    assignment["target"][
                        "deviceAndAppManagementAssignmentFilterType"
                    ],
                    assignment["target"][
                        "deviceAndAppManagementAssignmentFilterId"
                    ],
                ]
            )

            assignment_list.sort(key=lambda x: x[0], reverse=True)  # Sort by the 'Intent' column in reverse order
            table = write_assignment_table(assignment_list, headers)

    return table


def remove_characters(string):
    """
    This function removes characters from the string.
    :param string: The string to be cleaned
    :return: The cleaned string
    """

    remove_chars = '#@}{]["'
    for char in remove_chars:
        string = string.replace(char, "")

    return string


def is_base64(s):
    """Check if a string is a valid base64-encoded string"""
    try:
        # Attempt to decode the string
        if isinstance(s, str):
            decoded = base64.b64decode(s.encode())
        else:
            decoded = base64.b64decode(s)
        # If decoding succeeds and the decoded bytes match the original string, it's a valid base64-encoded string
        return decoded == s.encode()
    except (TypeError, binascii.Error):
        # If decoding fails, it's not a valid base64-encoded string
        return False


def decode_base64(data):
    """
    This function decodes the data if it is base64 encoded.
    :param data: The data to be decoded
    :return: The decoded data
    """

    try:
        return base64.b64decode(data).decode("utf-8")
    except (base64.binascii.Error, UnicodeDecodeError):
        raise ValueError("Unable to decode data")


def _format_value_for_markdown(value):
    """
    Format setting value for markdown display, handling XML/JSON structures.
    If XML, wrap in <details> block with summary and code block.
    :param value: The setting value to format
    :return: Formatted value string
    """
    if not value or value == "Not configured":
        return value

    value_str = str(value)
    # Check if this looks like XML content
    if value_str.strip().startswith('<') and value_str.strip().endswith('>'):
        return (
            f"<details class='description'><summary data-open='Minimize' data-close='...expand...'></summary>\n\n"
            f"```xml\n{value_str.strip()}\n```\n\n"
            f"</details>"
        )
    # JSON pretty print (optional, keep as is)
    elif (value_str.strip().startswith('{') and value_str.strip().endswith('}')) or \
       (value_str.strip().startswith('[') and value_str.strip().endswith(']')):
        try:
            import json
            parsed = json.loads(value_str)
            formatted_json = json.dumps(parsed, indent=2)
            return f"\n\n```json\n{formatted_json}\n```\n\n"
        except Exception:
            pass
    return value_str


def clean_list(data, decode):
    """
    This function returns a list with strings to be used in a table.
    :param data: The data to be cleaned
    :return: The list of strings
    """

    def list_to_string(item_list) -> str:
        string = ""
        for i in item_list:
            if isinstance(i, (str, int, bool)):
                if decode and is_base64(i):
                    i = decode_base64(i)
                i = _format_value_for_markdown(i)
                string += f"<li> {i} </li>"
            elif isinstance(i, dict):
                string += dict_to_string(i)
            else:
                string += i

        return string

    def dict_to_string(d) -> str:
        string = ""
        for key, val in d.items():
            if isinstance(val, list):
                string += f"**{key}:** <ul>"
                string += list_to_string(val)
                string += "</ul>"
            elif isinstance(val, dict):
                string += dict_to_ul(val)
            else:
                string += simple_value_to_string(key, val)

        string += "<br/>"

        return string

    def dict_to_ul(val) -> str:
        string = ""
        for k, v in val.items():
            if isinstance(v, list):
                string += f"**{k}:** <ul>"
                string += list_to_string(v)
                string += "</ul>"
            elif isinstance(v, dict):
                string += f"**{k}:** <ul>"
                string += dict_to_ul(v)
                string += "</ul>"
            else:
                string += simple_value_to_string(k, v)
        return string

    def simple_value_to_string(key, val) -> str:
        if decode and is_base64(val):
            val = decode_base64(val)
        val = _format_value_for_markdown(val)
        if isinstance(val, str):
            val = val.replace("\\", "\\\\")

        return f"**{key}:** {val}<br/>"

    def list_string(item_list) -> str:
        string = ""
        for i in item_list:
            if isinstance(i, (str, int, bool)):
                if decode and is_base64(i):
                    i = decode_base64(i)
                i = _format_value_for_markdown(i)
                string += f"{i}<br/>"
            if isinstance(i, list):
                string += list_to_string(i)
            if isinstance(i, dict):
                string += dict_to_string(i)

        return string

    def string(s) -> str:
        if decode and is_base64(s):
            s = decode_base64(s)
        s = _format_value_for_markdown(s)
        if  len(s) > 200 and not s.startswith('<details'):
            string = f"<details><summary>Click to expand...</summary>{s}</details>"
        else:
            string = s

        return string

    values = []

    for item in data:
        if isinstance(item, list):
            values.append(list_string(item))
        elif isinstance(item, dict):
            values.append(dict_to_ul(item))
        elif isinstance(item, str):
            values.append(string(item))
        elif isinstance(item, (bool, int)):
            values.append(item)
        else:
            values.append(item)

    return values


def write_type_header(split, outpath, header):
    """
    This function writes the header to the Markdown document.

    :param outpath: The path to save the Markdown document to
    :param header: Header of the configuration being documented
    """
    if not split:
        with open(outpath, "a", encoding="utf-8") as md:
            md.write("# " + header + "\n")


def document_configs(
    configpath,
    outpath,
    header,
    max_length,
    split,
    cleanup,
    decode,
    split_per_config=False,
):
    """
    Documents configurations, optionally splitting by type or per config.

    :param configpath: Path to backup files
    :param outpath: Base path for Markdown output
    :param header: Configuration type header (e.g., "AppConfigurations")
    :param max_length: Max length for displayed values
    :param split: Split into one file per type
    :param cleanup: Remove empty values
    :param decode: Decode base64 values
    :param split_per_config: Split into one file per individual config
    """
    if not os.path.exists(configpath):
        return

    # Base file for non-split or type-split mode
    if split and not split_per_config:
        outpath = os.path.join(configpath, f"{header}.md")
        md_file(outpath)

    if split_per_config is False:
        with open(outpath, "a", encoding="utf-8") as md:
            md.write("## " + header + "\n")

    # Use recursive pattern to catch deeper structures
    pattern = os.path.join(
        configpath, "**", "*.[jy][sa][mo][nl]"
    )  # Matches .json, .yaml, .yml
    files = sorted(glob.glob(pattern, recursive=True), key=str.casefold)
    if not files:
        return

    for filename in files:
        if (
            filename.endswith(".md")
            or os.path.isdir(filename)
            or os.path.basename(filename) == ".DS_Store"
        ):
            continue

        try:
            # Load data
            with open(filename, encoding="utf-8") as f:
                if filename.endswith((".yaml", ".yml")):
                    repo_data = json.loads(json.dumps(yaml.safe_load(f)))
                elif filename.endswith(".json"):
                    repo_data = json.load(f)
                else:
                    continue

            # Prepare assignments table
            assignments_table = assignment_table(repo_data)
            repo_data.pop("assignments", None)

            # Handle description
            description = repo_data.pop("description", "") or ""

            # Build config table
            config_table_list = []
            for key, value in zip(
                repo_data.keys(), clean_list(repo_data.values(), decode)
            ):
                if cleanup and not value and not isinstance(value, bool):
                    continue
                if key == "@odata.type":
                    key = "Odata type"
                else:
                    key = " ".join(re.findall("[A-Z][^A-Z]*", key[0].upper() + key[1:]))
                if max_length and isinstance(value, str) and len(value) > max_length:
                    value = "Value too long to display"
                config_table_list.append([key, value])

            config_table = write_table(config_table_list)

            # Determine output file and header
            config_name = repo_data.get(
                "displayName",
                repo_data.get(
                    "name",
                    os.path.splitext(os.path.basename(filename))[0]
                    .replace("_", " ")
                    .title(),
                ),
            )
            if split_per_config:
                # One file per config
                safe_config_name = re.sub(
                    r'[<>:"/\\|?*]', "_", config_name
                )  # Sanitize filename
                if not os.path.exists(f"{configpath}/docs"):
                    os.makedirs(f"{configpath}/docs")
                config_outpath = os.path.join(
                    f"{configpath}/docs", f"{safe_config_name}.md"
                )
                md_file(config_outpath)
                target_md = config_outpath
                top_header = f"# {config_name}"
                split_per_config_index_md(configpath, header)
            elif split:
                # One file per type
                target_md = outpath
                top_header = f"### {config_name}"
            else:
                # Single file
                target_md = outpath
                top_header = f"### {config_name}"

            # Write to file
            with open(target_md, "a", encoding="utf-8") as md:
                md.write(top_header + "\n")
                if description:
                    md.write(f"Description: {escape_markdown(description)}\n")
                if assignments_table:
                    md.write("#### Assignments\n")
                    md.write(str(assignments_table) + "\n")
                md.write("#### Configuration\n")
                md.write(str(config_table) + "\n")

        except Exception as e:
            print(f"[DEBUG] Error processing {filename}: {type(e).__name__}: {e}")


def document_management_intents(configpath, outpath, header, split):
    """
    This function documents the management intents.

    :param configpath: The path to where the backup files are saved
    :param outpath: The path to save the Markdown document to
    :param header: Header of the configuration being documented
    :param split: Split documentation into multiple files
    """

    # If configurations path exists, continue
    if os.path.exists(configpath):
        if split:
            outpath = configpath + "/" + header + ".md"
            md_file(outpath)

        with open(outpath, "a", encoding="utf-8") as md:
            md.write("## " + header + "\n")

        pattern = configpath + "*/*"
        for filename in sorted(glob.glob(pattern, recursive=True), key=str.casefold):
            # If path is Directory, skip
            if os.path.isdir(filename):
                continue
            # If file is .DS_Store, skip
            if filename == ".DS_Store":
                continue

            # Check which format the file is saved as then open file, load data and set query parameter
            with open(filename, encoding="utf-8") as f:
                if filename.endswith(".yaml"):
                    data = json.dumps(yaml.safe_load(f))
                    repo_data = json.loads(data)
                elif filename.endswith(".json"):
                    f = open(filename, encoding="utf-8")
                    repo_data = json.load(f)
                else:
                    continue

                # Create assignments table
                assignments_table = ""
                assignments_table = assignment_table(repo_data)
                repo_data.pop("assignments", None)

                intent_settings_list = []
                for setting in repo_data["settingsDelta"]:
                    setting_definition = setting["definitionId"].split("_")[1]
                    setting_definition = (
                        setting_definition[0].upper() + setting_definition[1:]
                    )
                    setting_definition = re.findall("[A-Z][^A-Z]*", setting_definition)
                    setting_definition = " ".join(setting_definition)

                    vals = []
                    value = str(remove_characters(setting["valueJson"]))
                    comma = re.findall("[:][^:]*", value)
                    for v in value.split(","):
                        v = v.replace(" ", "")
                        if comma:
                            v = f'**{v.replace(":", ":** ")}'
                        vals.append(v)
                    value = ",".join(vals)
                    value = value.replace(",", "<br />")

                    intent_settings_list.append([setting_definition, value])

                repo_data.pop("settingsDelta")

                description = ""
                if "description" in repo_data:
                    if repo_data["description"] is not None:
                        description = repo_data["description"]
                        repo_data.pop("description")

                intent_table_list = []

                for key, value in zip(
                    repo_data.keys(), clean_list(repo_data.values(), decode=False)
                ):
                    key = key[0].upper() + key[1:]
                    key = re.findall("[A-Z][^A-Z]*", key)
                    key = " ".join(key)

                    if value and isinstance(value, str):
                        if len(value.split(",")) > 1:
                            vals = []
                            for v in value.split(","):
                                v = v.replace(" ", "")
                                v = f'**{v.replace(":", ":** ")}'
                                vals.append(v)
                            value = ",".join(vals)
                            value = value.replace(",", "<br />")

                    intent_table_list.append([key, value])

                table = intent_table_list + intent_settings_list

                config_table = write_table(table)
                # Write data to file
                with open(outpath, "a", encoding="utf-8") as md:
                    if "displayName" in repo_data:
                        md.write("### " + repo_data["displayName"] + "\n")
                    if "name" in repo_data:
                        md.write("### " + repo_data["name"] + "\n")
                    if description:
                        md.write(f"Description: {escape_markdown(description)} \n")
                    if assignments_table:
                        md.write("#### Assignments \n")
                        md.write(str(assignments_table) + "\n")
                    md.write("#### Configuration \n")
                    md.write(str(config_table) + "\n")


def split_per_config_index_md(configpath, header):
    """
    This function creates an index Markdown file for split_per_config mode.
    :param configpath: The path to where the backup files are saved
    :param outpath: The path to save the Markdown document to
    :param header: Header of the configuration being documented
    """
    # get all md files from the docs directory
    files = get_docs_md_files(configpath)
    index_md = f"{configpath}/{header}.md"
    md_file(index_md)

    with open(index_md, "w", encoding="utf-8") as doc:
        l1 = f"# {header} \n\n"
        l2 = "## File index \n\n"
        doc.writelines([l1, l2])
        for file in files:
            doc.writelines(
                [
                    "[",
                    str(file).split("/")[-1],
                    "](",
                    str(file).replace(" ", "%20"),
                    ") \n\n",
                ]
            )


def get_docs_md_files(configpath):
    """
    This function gets the Markdown files in the configpath/docs directory.
    :return: List of Markdown files
    """
    slash = "/"
    md_files = []
    client_os = platform.uname().system
    mdpath = configpath + "/docs/*.md"
    if client_os == "Windows":
        slash = "\\"
    for filename in glob.glob(mdpath):
        md_files.append(f"./docs/{filename.split(slash)[-1]}")
    return md_files


def get_md_files(configpath):
    """
    This function gets the Markdown files in the configpath directory.
    :return: List of Markdown files
    """
    slash = "/"
    client_os = platform.uname().system
    if client_os == "Windows":
        slash = "\\"
    md_files = []
    patterns = ["*/*.md", "*/*/*.md", "*/*/*/*.md", "*/*/*/*/*.md"]
    for pattern in patterns:
        for filename in glob.glob(configpath + pattern, recursive=True):
            # if folder name is docs, skip
            if "docs" in filename:
                continue
            filepath = filename.split(slash)
            configpathname = configpath.split(slash)[-1]
            filepath = filepath[filepath.index(configpathname) :]
            filepath = "/".join(filepath[1:])
            ignore_files = ["README", "index", "prod-as-built"]
            file_basename = os.path.splitext(filepath.rsplit("/", maxsplit=1)[-1])[0]
            if file_basename not in ignore_files:
                md_files.append(f"./{filepath}")
    # Sort the list alphabetically by file name without extension, case-insensitive
    md_files.sort(key=lambda f: os.path.splitext(os.path.basename(f))[0].lower())

    return md_files


def document_settings_catalog(
    configpath, outpath, header, split, split_per_config=False
):
    """
    Specialized documentation function for Settings Catalog policies.
    Creates simplified configuration sections and organized setting tables by category.

    :param configpath: Path to backup files
    :param outpath: Base path for Markdown output
    :param header: Configuration type header
    :param split: Split into one file per type
    :param split_per_config: Split into one file per individual config
    """
    if not os.path.exists(configpath):
        return

    # Base file for non-split or type-split mode
    if split and not split_per_config:
        outpath = os.path.join(configpath, f"{header}.md")
        md_file(outpath)

    if split_per_config is False:
        with open(outpath, "a", encoding="utf-8") as md:
            md.write("## " + header + "\n")

    # Use recursive pattern to catch deeper structures
    pattern = os.path.join(
        configpath, "**", "*.[jy][sa][mo][nl]"
    )  # Matches .json, .yaml, .yml
    files = sorted(glob.glob(pattern, recursive=True), key=str.casefold)
    if not files:
        return

    for filename in files:
        if (
            filename.endswith(".md")
            or os.path.isdir(filename)
            or os.path.basename(filename) == ".DS_Store"
        ):
            continue

        try:
            # Load data
            with open(filename, encoding="utf-8") as f:
                if filename.endswith((".yaml", ".yml")):
                    repo_data = json.loads(json.dumps(yaml.safe_load(f)))
                elif filename.endswith(".json"):
                    repo_data = json.load(f)
                else:
                    continue

            # Prepare assignments table
            assignments_table = assignment_table(repo_data)

            # Extract basic policy information
            policy_name = repo_data.get("name", "Unknown Policy")
            description = repo_data.get("description", "")
            platform = repo_data.get("platforms", "")
            technologies = repo_data.get("technologies", "")
            scope_tags = repo_data.get("roleScopeTagIds", [])
            created_date = repo_data.get("createdDateTime", "")
            modified_date = repo_data.get("lastModifiedDateTime", "")

            # Create basic policy info table
            basics_table_data = [
                ["Name", policy_name],
                ["Description", description.replace('\n', ' ')] if description else None,
                ["Profile type", "Settings catalog"],
                ["Platform supported", _format_platform(platform)],
                ["Technologies", technologies],
                ["Scope tags", ", ".join(scope_tags) if scope_tags else "Default"]
            ]

            # Add dates if available
            if created_date:
                basics_table_data.append(["Created", _format_date(created_date)])
            if modified_date:
                basics_table_data.append(["Last modified", _format_date(modified_date)])

            # Remove None entries
            basics_table_data = [item for item in basics_table_data if item is not None]

            basics_table = _write_clean_table(["Setting", "Value"], basics_table_data)

            # Process settings by category
            settings = repo_data.get("settings", [])
            settings_tables = _create_settings_tables(settings)

            # Determine output file and header
            if split_per_config:
                # One file per config
                safe_config_name = re.sub(r'[<>:"/\\|?*]', "_", policy_name)
                if not os.path.exists(f"{configpath}/docs"):
                    os.makedirs(f"{configpath}/docs")
                config_outpath = os.path.join(
                    f"{configpath}/docs", f"{safe_config_name}.md"
                )
                md_file(config_outpath)
                target_md = config_outpath
                top_header = f"# {policy_name}"
                split_per_config_index_md(configpath, header)
            elif split:
                # One file per type
                target_md = outpath
                top_header = f"### {policy_name}"
            else:
                # Single file
                target_md = outpath
                top_header = f"### {policy_name}"

            # Write to file
            with open(target_md, "a", encoding="utf-8") as md:
                md.write(top_header + "\n\n")

                if assignments_table:
                    md.write("#### Assignments\n")
                    md.write(str(assignments_table) + "\n\n")

                md.write("#### Basics\n")
                md.write(str(basics_table) + "\n\n")

                # Write single configuration table
                if settings_tables:
                    # There should only be one table now
                    for category_name, table in settings_tables:
                        md.write(f"#### {category_name}\n")
                        md.write(str(table) + "\n\n")

        except Exception as e:
            print(f"[DEBUG] Error processing Settings Catalog {filename}: {type(e).__name__}: {e}")


def _format_platform(platform):
    """Format platform string to be more readable."""
    platform_map = {
        "windows10": "Windows 10 and later",
        "macOS": "macOS",
        "iOS": "iOS/iPadOS",
        "android": "Android"
    }
    return platform_map.get(platform, platform)


def _format_date(date_string):
    """Format ISO date string to readable format."""
    try:
        from datetime import datetime
        # Parse ISO format and convert to readable format
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return date_string


def _create_settings_tables(settings):
    """
    Create a settings table grouped and sorted by categoryDisplayName, with a visually distinctive row for each category.
    """
    if not settings:
        return []

    # Build a lookup for all definitions by id for fast access
    def build_definitions_lookup(settings):
        lookup = {}
        for setting in settings:
            for definition in setting.get("settingDefinitions", []):
                lookup[definition["id"]] = definition
        return lookup

    definitions_lookup = build_definitions_lookup(settings)

    # Group settings by categoryDisplayName
    category_map = {}
    for setting in settings:
        # Get the main definition for this setting
        main_def = setting.get("settingDefinitions", [{}])[0]
        category = main_def.get("categoryDisplayName", "Other Settings")
        if category not in category_map:
            category_map[category] = []
        parent_definitions = {d["id"]: d for d in setting.get("settingDefinitions", [])}
        setting_instance = setting.get("settingInstance")
        if setting_instance:
            # Use your existing extract_setting logic
            rows = _extract_setting_rows_for_category(setting_instance, parent_definitions, definitions_lookup)
            category_map[category].extend(rows)

    # Sort categories alphabetically
    sorted_categories = sorted(category_map.keys(), key=lambda x: x.lower())

    # Build the table rows with category headers
    table_rows = []
    for category in sorted_categories:
        # Add a visually distinctive row for the category
        table_rows.append([
            f"<tr style='background-color:#e0e0e0;font-weight:bold;'><td colspan='3'>{category}</td></tr>"
        ])
        # Add all settings for this category
        table_rows.extend(category_map[category])

    # Flatten rows for html_table (skip the header row from html_table, as we add our own)
    headers = ["Setting", "Value", "Description"]
    # html_table expects rows as lists, but our category row is a raw HTML string, so we need to handle this
    def custom_html_table(headers, rows):
        table = "<table>\n<thead><tr>"
        for h in headers:
            table += f"<th>{h}</th>"
        table += "</tr></thead>\n<tbody>\n"
        for row in rows:
            if isinstance(row, str) or (isinstance(row, list) and len(row) == 1 and row[0].startswith("<tr")):
                # Raw HTML row (category header)
                table += row[0] if isinstance(row, list) else row
            else:
                table += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>\n"
        table += "</tbody>\n</table>"
        return table

    table = custom_html_table(headers, table_rows)
    return [("Configuration", table)]


def _extract_setting_rows_for_category(setting_instance, parent_definitions, definitions_lookup):
    """
    Recursively extract setting rows for a category.
    """
    # Use your existing extract_setting logic, but return a list of [Setting, Value, Description] rows.
    def extract_setting(setting_instance, parent_definitions):
        setting_definition_id = setting_instance.get("settingDefinitionId", "")
        definition = parent_definitions.get(setting_definition_id) or definitions_lookup.get(setting_definition_id, {})
        display_name = definition.get("displayName", _format_setting_name(setting_definition_id))
        description = definition.get("description", "")
        if isinstance(description, str):
            description = re.sub(r'((\r\n|\r|\n){2,})', r'\r\n', description)
            description = description.rstrip(' \t')
            if len(description) > 60:
                description = (
                    f"<details><summary>...expand...</summary>"
                    f"{description}</details>"
                )

        if "simpleSettingValue" in setting_instance:
            value = setting_instance["simpleSettingValue"].get("value", "")
            formatted_value = _format_value_for_markdown(value if value != "" else "Not configured")
            return [[display_name, formatted_value, description]]

        elif "simpleSettingCollectionValue" in setting_instance:
            collection = setting_instance["simpleSettingCollectionValue"]
            if isinstance(collection, list) and collection:
                values = []
                for item in collection:
                    val = item.get("value", "")
                    if val != "":
                        values.append(str(val))
                if values:
                    formatted_value = _format_value_for_markdown(f"\n\n```\n" + "\n".join(values) + "\n```\n")
                else:
                    formatted_value = _format_value_for_markdown("Not configured")
                return [[display_name, formatted_value, description]]
            else:
                return [[display_name, "Not configured", description]]

        elif "choiceSettingValue" in setting_instance:
            choice_value_obj = setting_instance["choiceSettingValue"]
            value = choice_value_obj.get("value", "")
            children = choice_value_obj.get("children", [])
            option_display_name = None
            if value and "options" in definition:
                for option in definition["options"]:
                    if option.get("value") == value or option.get("itemId") == value:
                        option_display_name = option.get("displayName") or option.get("name")
                        break
            formatted_value = _format_value_for_markdown(option_display_name if option_display_name else (value if value else "Not configured"))
            rows = []
            rows.append([display_name, formatted_value, description])
            for child in children:
                rows.extend(extract_setting(child, parent_definitions))
            return rows

        elif "groupSettingCollectionValue" in setting_instance:
            collection = setting_instance["groupSettingCollectionValue"]
            rows = []
            if isinstance(collection, list):
                for item in collection:
                    children = item.get("children", [])
                    for child in children:
                        rows.extend(extract_setting(child, parent_definitions))
            return rows if rows else [[display_name, "Collection value", description]]

        return [[display_name, "Not configured", description]]

    return extract_setting(setting_instance, parent_definitions)


def _write_clean_table(headers, data):
    """
    Create a clean, compact HTML table.
    :param headers: List of column headers
    :param data: List of rows, each row is a list of values
    :return: Clean HTML table string
    """
    if not data:
        return ""
    return html_table(headers, data)


def _format_setting_name(setting_definition_id):
    """
    Format setting definition ID into a readable name.

    :param setting_definition_id: The setting definition ID
    :return: Formatted setting name
    """
    if not setting_definition_id:
        return "Unknown Setting"

    # Special cases for well-known settings
    if "machineinactivitylimit" in setting_definition_id.lower():
        return "Interactive Logon Machine Inactivity Limit"

    # Extract the meaningful part from the ID
    parts = setting_definition_id.split("_")

    # Find the last meaningful parts (usually after the category)
    if len(parts) > 3:
        # Take the last 2-3 parts and format them
        meaningful_parts = parts[-3:] if len(parts) > 5 else parts[-2:]
        # Join and format
        name = " ".join(meaningful_parts)
        # Convert to title case, handling version numbers
        name = re.sub(r'_v\d+$', '', name)  # Remove version suffix
        name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)  # Add spaces before capitals
        return name.title()

    # Fallback to just converting underscores to spaces and title case
    return setting_definition_id.replace("_", " ").title()


def _extract_setting_value(setting_instance):
    """
    Extract the value from a setting instance, including children values.

    :param setting_instance: The setting instance object
    :return: Formatted setting value or list of child values
    """
    if "simpleSettingValue" in setting_instance:
        value = setting_instance["simpleSettingValue"].get("value", "")
        return value if value != "" else "Not configured"
    elif "choiceSettingValue" in setting_instance:
        choice_value_obj = setting_instance["choiceSettingValue"]

        # Check if there are children with actual values
        if "children" in choice_value_obj and choice_value_obj["children"]:
            child_values = []
            for child in choice_value_obj["children"]:
                child_value = _extract_setting_value(child)
                if child_value and child_value != "Not configured" and child_value != "":
                    child_values.append(child_value)

            # If we found child values, return them; otherwise fall back to choice value
            if child_values:
                return child_values if len(child_values) > 1 else child_values[0]

        # Fallback to choice value
        choice_value = choice_value_obj.get("value", "")
        if choice_value:
            # Try to extract meaningful part from choice value
            if "_" in choice_value:
                parts = choice_value.split("_")
                if len(parts) > 1:
                    meaningful_part = parts[-1]
                    # Return the meaningful part, but only if it's not just "selected"
                    if meaningful_part.lower() not in ["selected", "enabled", "disabled"]:
                        return meaningful_part.title()
            return choice_value
        return "Not configured"
    elif "groupSettingCollectionValue" in setting_instance:
        collection = setting_instance["groupSettingCollectionValue"]
        if isinstance(collection, list) and len(collection) > 0:
            extracted = []
            for item in collection:
                # If the item has children, extract their values
                if "children" in item and item["children"]:
                    child_values = []
                    for child in item["children"]:
                        child_value = _extract_setting_value(child)
                        if child_value and child_value != "Not configured" and child_value != "":
                            child_values.append(child_value)
                    if child_values:
                        # If only one value, don't wrap in list
                        extracted.append(child_values if len(child_values) > 1 else child_values[0])
                else:
                    # Fallback: try to extract value directly
                    value = item.get("value", None)
                    if value:
                        extracted.append(value)
            # Flatten if only one item
            if len(extracted) == 1:
                return extracted[0]
            return extracted if extracted else "Not configured"
        return "Collection value"

    return "Not configured"
