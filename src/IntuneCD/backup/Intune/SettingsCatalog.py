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
        Verrijkt settings met alleen de hoofd settingDefinition van elke settingInstance.
        Slaat deze op onder 'settingDefinitions' in de JSON, met id, name, displayName, description
        en indien aanwezig de options (itemId, name, value).
        """
        if not settings:
            return settings

        # Verzamel alleen de hoofd settingDefinitionIds
        definition_ids = set()
        for setting in settings:
            if "settingInstance" in setting and isinstance(setting["settingInstance"], dict):
                def_id = setting["settingInstance"].get("settingDefinitionId")
                if def_id:
                    definition_ids.add(def_id)

        if not definition_ids:
            return settings

        # Haal alle hoofd settingDefinitions op via Graph
        definition_map = {}
        try:
            for def_id in definition_ids:
                try:
                    definition = self.make_graph_request(
                        endpoint=f"{self.endpoint}/beta/deviceManagement/configurationSettings/{def_id}"
                    )
                    # Bouw de gewenste structuur
                    definition_entry = {
                        "id": definition.get("id", ""),
                        "name": definition.get("name", ""),
                        "displayName": definition.get("displayName", ""),
                        "description": definition.get("description", "")
                    }
                    # Voeg options toe indien aanwezig
                    if "options" in definition and isinstance(definition["options"], list):
                        definition_entry["options"] = []
                        for option in definition["options"]:
                            definition_entry["options"].append({
                                "itemId": option.get("itemId", ""),
                                "name": option.get("name", ""),
                                "value": option.get("optionValue", {}).get("value", None)
                            })
                    definition_map[def_id] = definition_entry
                except Exception as e:
                    self.log(
                        tag="warning",
                        msg=f"Could not retrieve definition for {def_id}: {e}"
                    )
                    continue
        except Exception as e:
            self.log(
                tag="warning",
                msg=f"Error enriching settings with definitions: {e}"
            )
            return settings

        # Voeg de settingDefinitions toe aan elke setting (alleen hoofd settingDefinitionId)
        enriched_settings = []
        for setting in settings:
            enriched_setting = setting.copy()
            def_id = None
            if "settingInstance" in setting and isinstance(setting["settingInstance"], dict):
                def_id = setting["settingInstance"].get("settingDefinitionId")
            if def_id and def_id in definition_map:
                enriched_setting["settingDefinitions"] = [definition_map[def_id]]
            else:
                enriched_setting["settingDefinitions"] = []
            enriched_settings.append(enriched_setting)

        return enriched_settings
