import json

class TelemetryDataTransferTypes:
    TELEMETRY_TYPES_FILEPATH = "src/telemetry_data_transfer_types.json"

    def __init__(self):
        self._telemetry_data_transfer_types: dict[str, dict[str, any]] = self._load_telemetry_data_transfer_types()


    def _load_telemetry_data_transfer_types(self) -> dict[str, dict[str, any]]:
        """
        Load telemetry data transfer types.
        """
        # Load the telemetry data transfer types from the JSON
        with open(TelemetryDataTransferTypes.TELEMETRY_TYPES_FILEPATH, "r", encoding="utf-8") as f:
            telemetry_data_transfer_types = json.load(f)
        return telemetry_data_transfer_types
        

    def is_type_label_valid_for_category(self, category: str, label: str) -> bool:
        """
        Check if a type label is valid for a given category.
        """
        return label in self._telemetry_data_transfer_types.get(category, {}).keys()
    

    def is_type_for_label_in_category_valid(self, category: str, label: str, data: any) -> bool:
        """
        Check if a type is valid for a given label in a category.
        """
        if not self.is_type_label_valid_for_category(category, label):
            return False
        # Get the expected type for the label in the category
        expected_type = self._telemetry_data_transfer_types[category][label]

        # Process the type
        if isinstance(expected_type, str):
            expected_type = self.convert_string_type_to_python_type(expected_type)
        elif isinstance(expected_type, dict):
            expected_type = {key: self.convert_string_type_to_python_type(val) for key, val in expected_type.items()}
        else:
            expected_type = type(expected_type)

        return isinstance(data, expected_type)
    
    def get_index_of_category_and_label(self, category: str, label: str) -> tuple[int, int] | None:
        """
        Get the index of a category and label in the telemetry data transfer types.
        """
        if not self.is_type_label_valid_for_category(category, label):
            return None
        return list(self._telemetry_data_transfer_types.keys()).index(category), list(self._telemetry_data_transfer_types[category].keys()).index(label)
    
    def convert_string_type_to_python_type(self, type_str: str) -> type:
        """
        Convert a string type to a Python type.
        """
        type_mapping = {
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            "list": list,
            "dict": dict,
            # Add more types as needed
        }
        return type_mapping.get(type_str, None)