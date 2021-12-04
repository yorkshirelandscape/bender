import markovify
import json


class Brain:
    def __init__(self, path):
        self.path = path
        self.messages = {}
        self.models = []

    def load_from_file(self):
        with open(self.path, "r") as json_file:
            self.messages = json.loads(json_file.read())

    def write_file(self):
        with open(self.path, "w") as json_file:
            json_file.write(json.dumps(self.messages))

    def learn_new_messages(self, new_messages, *, model_max):
        self.messages.update(new_messages)
        self.write_file()

        self.models = [
            markovify.Text(self.all_messages_as_string(), i + 1).compile()
            for i in range(model_max)
        ]

        # logging.info(f"learned {len(new_messages)} new messages")

    def all_messages_as_string(self):
        return " ".join(self.messages.values())
