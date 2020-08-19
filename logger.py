import datetime


class Logger:

	def __init__(self):
		self.log_file = open('events.log', 'a', encoding='utf-8')
		self.log_file.write('--- START PROGRAM ------------------------------------------------------------------------\n')

	def __del__(self):
		self.log_file.write('---- STOP PROGRAM ------------------------------------------------------------------------\n')
		self.log_file.write('\n')
		self.log_file.close()

	def log(self, message: str):
		self.log_file.write(f'[{datetime.datetime.today().strftime("%Y-%m-%d %H.%M.%S.%f")}] : {message}\n')
