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
        Enrich settings with display names and descriptions from setting definitions.
        This method retrieves additional metadata from Microsoft Graph API to make 
        Settings Catalog documentation more readable and user-friendly.
        
        :param settings: List of settings from the policy
        :return: List of enriched settings with displayName and description
        """
        if not settings:
            return settings
            
        # Collect unique setting definition IDs to batch request definitions
        definition_ids = set()
        for setting in settings:
            if "settingDefinitions" in setting:
                for definition in setting["settingDefinitions"]:
                    if "id" in definition:
                        definition_ids.add(definition["id"])
        
        if not definition_ids:
            return settings
            
        # Get setting definitions to retrieve display names and descriptions
        try:
            # Convert set to list for batch request
            definition_ids_list = list(definition_ids)
            definition_responses = []
            
            # Make requests for setting definitions in batches
            for i in range(0, len(definition_ids_list), 20):  # Process in chunks of 20
                batch_ids = definition_ids_list[i:i+20]
                for def_id in batch_ids:
                    try:
                        definition_response = self.make_graph_request(
                            endpoint=f"{self.endpoint}/beta/deviceManagement/configurationSettings/{def_id}"
                        )
                        definition_responses.append(definition_response)
                    except Exception as e:
                        self.log(
                            tag="warning", 
                            msg=f"Could not retrieve definition for {def_id}: {e}"
                        )
                        continue
            
            # Create mapping of definition ID to display name and description
            definition_map = {}
            for definition in definition_responses:
                if "id" in definition:
                    definition_map[definition["id"]] = {
                        "displayName": definition.get("displayName", ""),
                        "description": definition.get("description", "")
                    }
            
            # Enrich settings with display names and descriptions
            enriched_settings = []
            for setting in settings:
                enriched_setting = setting.copy()
                if "settingDefinitions" in setting:
                    enriched_definitions = []
                    for definition in setting["settingDefinitions"]:
                        if "id" in definition and definition["id"] in definition_map:
                            enriched_definition = definition.copy()
                            enriched_definition.update(definition_map[definition["id"]])
                            enriched_definitions.append(enriched_definition)
                        else:
                            enriched_definitions.append(definition)
                    enriched_setting["settingDefinitions"] = enriched_definitions
                enriched_settings.append(enriched_setting)
                
            return enriched_settings
            
        except Exception as e:
            self.log(
                tag="warning", 
                msg=f"Error enriching settings with definitions: {e}"
            )
            return settings
