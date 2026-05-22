import os
import json


class Config:

    def __init__(self):

        self._line_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN","")
        self._group_id = os.getenv("LINE_GROUP_ID","")

    @property
    def line_access_token(self):
        return self._line_access_token

    @property
    def group_id(self):
        return self._group_id

    def to_dict(self):
        return {
            "LINE_CHANNEL_ACCESS_TOKEN": self._line_access_token,
            "LINE_GROUP_ID": self._group_id,
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4)

config = Config()

if __name__ == "__main__":

    print("=== CONFIG TEST ===")
    print()

    print("LINE ACCESS TOKEN:")
    print(config.line_access_token)
    print()

    print("GROUP ID:")
    print(config.group_id)
    print()

    print("JSON OUTPUT:")
    print(config.to_json())
