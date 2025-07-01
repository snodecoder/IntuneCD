# -*- coding: utf-8 -*-
from ...intunecdlib.BaseBackupModule import BaseBackupModule


class SettingsCatalogBackupModule(BaseBackupModule):
    """A class used to backup Intune Settings Catalog

    Attributes:
        CONFIG_ENDPOINT (str): The endpoint to get the data from
        LOG_MESSAGE (str): The message to log when backing up the data
    """

    CONFIG_ENDPOINT = "/beta/deviceManagement/configurationPolicies"
    LOG_MESSAGE = "Backing up Settings Catalog Policy: "

    def __init__(self, *args, **kwargs):
        """Initializes the SettingsCatalogBackupModule class

        Args:
            *args: The positional arguments to pass to the base class's __init__ method.
            **kwargs: The keyword arguments to pass to the base class's __init__ method.
        """
        super().__init__(*args, **kwargs)
        self.path = f"{self.path}/Settings Catalog/"
        self.audit_filter = (
            self.audit_filter or "componentName eq 'DeviceConfiguration'"
        )
        self.assignment_endpoint = "deviceManagement/configurationPolicies/"
        self.assignment_extra_url = "/assignments"
        self.config_audit_data = True

    def main(self) -> dict[str, any]:
        """The main method to backup the Settings Catalog

        Returns:
            dict[str, any]: The results of the backup
        """
        try:
            self.graph_data = self.make_graph_request(
                endpoint=self.endpoint + self.CONFIG_ENDPOINT
            )
        except Exception as e:
            self.log(
                tag="error",
                msg=f"Error getting Settings Catalog data from {self.endpoint + self.CONFIG_ENDPOINT}: {e}",
            )
            return None

        item_ids = [item["id"] for item in self.graph_data["value"]]
        item_ids_dict = [{"id": item_id} for item_id in item_ids]
        # As we need to process each item individually, get the assignments up front
        self.assignment_responses = self.batch_assignment(
            item_ids_dict, self.assignment_endpoint, self.assignment_extra_url
        )
        # As we need to process each item individually, get the audit data up front
        if self.audit:
            self.audit_data = self.make_audit_request(self.audit_filter)
        # Get the settings for each policy using batch request
        policy_responses = self.batch_request(
            item_ids, "deviceManagement/configurationPolicies/", "/settings?&top=1000"
        )

        for item in self.graph_data["value"]:
            settings = self.get_object_details(item["id"], policy_responses)
            if settings:
                # Enhance settings with display names from setting definitions
                # This improves documentation by providing human-readable setting names
                enriched_settings = self._enrich_settings_with_definitions(settings)
                item["settings"] = enriched_settings

            self.preset_filename = (
                f"{item['name']}_{str(item['technologies']).rsplit(',', 1)[-1]}"
            )

            try:
                results = self.process_data(
                    data=item,
                    filetype=self.filetype,
                    path=self.path,
                    name_key="name",
                    log_message=self.LOG_MESSAGE,
                    audit_compare_info={
                        "type": "resourceId",
                        "value_key": "id",
                    },
                )
                self.update_results(results)
            except Exception as e:
                self.log(
                    tag="error", msg=f"Error processing Settings Catalog data: {e}"
                )
                return None

        return self.results


    def _enrich_settings_with_definitions(self, settings: list) -> list:
        """
        Enrich settings with all relevant settingDefinitions (main and children).
        Each setting in the JSON will have a 'settingDefinitions' array with all unique definitions used in that settingInstance tree.
        """
        if not settings:
            return settings

        # Helper to recursively collect all definitionIds from a settingInstance
        def collect_definition_ids(instance):
            ids = set()
            if isinstance(instance, dict):
                def_id = instance.get("settingDefinitionId")
                if def_id:
                    ids.add(def_id)
                # Check for children in choiceSettingValue, groupSettingCollectionValue, etc.
                if "choiceSettingValue" in instance and "children" in instance["choiceSettingValue"]:
                    for child in instance["choiceSettingValue"]["children"]:
                        ids.update(collect_definition_ids(child))
                if "groupSettingCollectionValue" in instance:
                    for group in instance["groupSettingCollectionValue"]:
                        if "children" in group:
                            for child in group["children"]:
                                ids.update(collect_definition_ids(child))
                if "simpleSettingValue" in instance and isinstance(instance["simpleSettingValue"], dict):
                    # No children for simpleSettingValue
                    pass
            return ids

        # Collect all unique definitionIds needed for all settings
        all_definition_ids = set()
        setting_to_ids = []
        for setting in settings:
            ids = set()
            if "settingInstance" in setting and isinstance(setting["settingInstance"], dict):
                ids = collect_definition_ids(setting["settingInstance"])
            setting_to_ids.append(ids)
            all_definition_ids.update(ids)

        if not all_definition_ids:
            return settings

        # Retrieve all definitions from Graph and build a map
        definition_map = {}
        try:
            # Batch request for all definitionIds
            batched_definitions = self.make_graph_request(
                endpoint=f"{self.endpoint}/beta/deviceManagement/configurationSettings",
                params={"ids": ",".join(all_definition_ids)}
            )
            for definition in batched_definitions.get("value", []):
                entry = {
                    "id": definition.get("id", ""),
                    "name": definition.get("name", ""),
                    "displayName": definition.get("displayName", ""),
                    "description": definition.get("description", "")
                }
                # Add options if present
                if "options" in definition and isinstance(definition["options"], list):
                    entry["options"] = []
                    for option in definition["options"]:
                        entry["options"].append({
                            "itemId": option.get("itemId", ""),
                            "name": option.get("name", ""),
                            "displayName": option.get("displayName", ""),
                            "value": option.get("optionValue", {}).get("value", None)
                        })
                # Add categoryDisplayName for the main (root) setting definition
                if "categoryId" in definition:
                    try:
                        rootCategoryId = self.make_graph_request(
                            endpoint=f"{self.endpoint}/beta/deviceManagement/configurationCategories/{definition['categoryId']}?$select=rootCategoryId"
                        )
                        category = self.make_graph_request(
                            endpoint=f"{self.endpoint}/beta/deviceManagement/configurationCategories/{rootCategoryId['rootCategoryId']}?$select=displayName"
                        )
                        entry["categoryDisplayName"] = category.get("displayName", "")
                    except Exception as e:
                        self.log(
                            tag="warning",
                            msg=f"Could not retrieve category for {def_id}: {e}"
                        )
                        entry["categoryDisplayName"] = ""
                definition_map[def_id] = entry
            except Exception as e:
                self.log(
                    tag="warning",
                    msg=f"Could not retrieve definition for {def_id}: {e}"
                )
                continue

        # Add all relevant definitions to each setting
        enriched_settings = []
        for setting, ids in zip(settings, setting_to_ids):
            enriched_setting = setting.copy()
            enriched_setting["settingDefinitions"] = [definition_map[i] for i in ids if i in definition_map]
            enriched_settings.append(enriched_setting)

        return enriched_settings
