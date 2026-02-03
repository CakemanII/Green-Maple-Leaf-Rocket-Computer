import json

class CommandIDMapping:
    @staticmethod
    def id_to_command(map_location: str, id: str) -> str:
        with open(map_location, "r") as file:
            mapping = json.load(file)
        return mapping.get(id, "UNKNOWN_COMMAND")

    @staticmethod
    def command_to_id(map_location: str, command: str) -> str:
        with open(map_location, "r") as file:
            mapping = json.load(file)
        for id, cmd in mapping.items():
            if cmd == command:
                return id
        return "UNKNOWN_ID"