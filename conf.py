import json


class Conf:

	def __init__(self):
		self.load()

	def save(self):
		with open('configuration.json', 'w', encoding='utf-8') as f:
			json.dump(self.json_object, f, ensure_ascii=False, indent=4)

	def load(self):
		with open('configuration.json', 'r', encoding='utf-8') as f:
			self.json_object = json.load(f)

	def get(self, value: str):
		return self.json_object[value]
