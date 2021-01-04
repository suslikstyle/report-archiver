import locale
import py7zr
import os
import datetime
import re
import shutil
from conf import Conf
from logger import Logger


CREATE_ARCHIVE_PATH_ERROR_CODE = 2
OS_ERROR_CODE = 3

event = Logger()


class Item(object):

	def __init__(self, date: datetime, shift: int):
		self.date = date
		self.shift = shift

	def __repr__(self):
		return f"{self.date.strftime('%Y.%m.%d')} {'I' if self.shift == 1 else 'II'}.xls"

	def __eq__(self, other):
		return (self.shift == other.shift) and (self.date == other.date)

	def __contains__(self, item):
		return (item.date == self.date) and (item.shift == self.shift)


class MonthItem(object):
	"""
	Класс...
	"""

	def __init__(self, year: int, month: int, path: str):
		"""
		Инициализация объекта, содержащего в себе информацию об отчетах за месяц
		:param year: год
		:param month: месяц 1..12
		:param path: каталог, в который переносятся отчеты.
		"""
		self._dataSet = []
		self._model = []
		self.year = year
		self.month = month
		self.path = path
		end_date = datetime.datetime(year + int(month / 12), ((month % 12) + 1), 1) - datetime.timedelta(days=1)
		# self._model = [Item(datetime.date(year, month, day), 1) for day in range(1, end_date.day+1, 1)]
		for day in range(1, end_date.day + 1, 1):
			self._model.append(Item(datetime.date(year=year, month=month, day=day), 1))
			self._model.append(Item(datetime.date(year=year, month=month, day=day), 2))

	def __del__(self):
		del self._dataSet

	def __repr__(self):
		result = [f"{item.date.strftime('%Y.%m.%d')} {'I' if item.shift == 1 else 'II'}.xls" for item in self._dataSet]
		return '\n'.join(result)

	def __bool__(self):
		return len(self._dataSet) == len(self._model)

	def __len__(self):
		return len(self._dataSet)

	def add(self, date: datetime, shift: int):
		self._dataSet.append(Item(date=date, shift=shift))

		if len(self._dataSet) >= len(self._model):
			event.log(f'Каталог "{self.path}" готов к архивированию...')
			print(f'Каталог "{self.path}" готов к архивированию...')

	def check(self):
		"""
		Пройти по списку шаблона, проверить каких отчетов нехватает. Вернуть список недостоющих
		:return: List
		"""
		return [item for item in self._model if item not in self._dataSet]


class Items(object):

	def __init__(self):
		self._data_set = {}
		self.archive_path = None

	def __del__(self):
		del self._data_set

	def add(self, date: datetime, shift: int, path: str):
		"""
		Добавить элемент
		:param date: дата в виде datetime объекта
		:param shift: Смена, int
		:param path: Каталог, в котором будет находится отчет
		:return: None
		"""
		if date.strftime('%Y-%m') not in self._data_set.keys():
			self._data_set[date.strftime('%Y-%m')] = MonthItem(year=date.year, month=date.month, path=path)

		self._data_set[date.strftime('%Y-%m')].add(date=date, shift=shift)

	def chk(self):
		a_list = [self._data_set[key].check() for key in self._data_set.keys() if not self._data_set[key]]
		func = lambda ll: [el for lst in ll for el in lst]
		return func(a_list)


items = Items()


def main():
	"""
	Точка входа в программу
	"""
	locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
	event.log('Запуск приложения.')
	report_path = ''
	archive_path = ''
	try:
		conf = Conf()		# Читаем конфиг файл
		report_path = conf.get("reportPath")
		archive_path = conf.get("archivePath")
		if not os.path.exists(archive_path):			# создать архивный каталог, если он отсутствует
			os.makedirs(archive_path)
			event.log(f'Создали архивный каталог: "{archive_path}", так как он отсутствовал.')
	except Exception as err:
		event.log(f'При создании каталога возникла ошибка: {err} Выход с кодом {CREATE_ARCHIVE_PATH_ERROR_CODE}')
		exit(CREATE_ARCHIVE_PATH_ERROR_CODE)

	try:
		names = os.listdir(report_path)		# Список имен файлов в папке с отчетами
		# Отправляем в обработчик каждый найденный файл
		for name in names:
			handler(report_path, name, archive_path)

		miss_list = items.chk()
		if len(miss_list) > 0:
			event.log(f"Недостающие отчеты: {miss_list}")
			print(f"Недостающие отчеты: {miss_list}")

		# проверка архивной папки на готовность к архивированию, упаковке
		compression(path=report_path, archive_path=archive_path)
	except OSError as err:
		print(f"Ошибка: {err} Выход с кодом {OS_ERROR_CODE}")
		exit(OS_ERROR_CODE)
	except Exception as err:
		event.log(f'Ошибка: {err}')
		exit(1)


def handler(path: str, name: str, archive: str):
	"""
		Обрабатываем каждый найденный файл.
		Архивируем отчет за прошлые месяца в архивную папку,
		если отчет за текущий месяц, оставляем без изменения.
	:param path: Путь к папке
	:param name: Имя файла
	:param archive: Путь к архивной папке (из конфига)
	:return: null
	"""
	fullname = os.path.join(path, name)
	if os.path.isfile(fullname):
		result = re.match(r'(\d{4})([.\-_])(\d{2})([.\-_])(\d{2})[_N\s]*(I{1,2})(\.xls)', name)
		try:
			date_str = result.group(1) + result.group(2) + result.group(3) + result.group(4) + result.group(5)
			date = datetime.datetime.strptime(date_str, "%Y{}%m{}%d".format(result.group(2), result.group(4))).date()
			if result.group(6) == 'I':
				smena = 1
			elif result.group(6) == 'II':
				smena = 2
			else:
				print('Смена может быть I или II.')
				return
			if datetime.datetime(date.year, date.month, 1) < \
					datetime.datetime(datetime.datetime.today().year, datetime.datetime.today().month, 1):
				# Отчеты прошлых месяцев обрабатываются тут
				new_path = os.path.join(path, f'{date.year}', "{}".format(date.strftime('%m %B')))
				new_name = os.path.join(new_path, name)
				if not os.path.exists(new_path):
					os.makedirs(new_path)

				# print(name, '=>', new_name)
				os.rename(fullname, new_name)
				event.log('Файл: "{}" перемещен в "{}"'.format(fullname, new_name))
				items.add(date, smena, new_path)
			else:
				# Тут обработка отчетов текщего месяца
				pass
				# print('"{}" - Отчет текущего месяца.'.format(name))
		except AttributeError:
			# print('"{}" скорее всего не файл отчета, пропускаем.'.format(name))
			event.log(f'Файл: "{name}" не похож на файл отчета, - пропускаем.')
		except ValueError as err:
			# print(name + ' пропуск файла отчета из-за ошибки', err)
			event.log(f'Файл: "{name}" был пропущен из-за ошибки: {err}')
		except Exception as err:
			# print('При обработке файла: {} возникла ошибка: {}'.format(name, err))
			event.log(f'При обработке файла: "{name}" возникла ошибка: {err}')
	else:		# Иначе fullname - это не файл
		event.log(f'Папка: "{name}" - пропускаем.')


def compression(path: str, archive_path: str):
	"""
	Проверка на готовность к упаковке папки с архивами, упаковка готовых папок
	:param archive_path: Каталог с архивами, из конфиг файла
	:param path: каталог с несортированными отчетами и сортированными по папками
	:return:
	"""
	event.log(f'Анализ каталога с архивами: {path}')
	names = os.listdir(path)
	for name in names:
		fullname = os.path.join(path, name)
		if os.path.isdir(fullname):
			# Проверяем наличие необходимых папок и отчетов
			try:
				result = re.match(r'(\d{4})', name)
				if result is not None:
					# Если папка состоит из 4 цифр создаем список содержимого этой папки (кривовато)
					months = os.listdir(fullname)
					if len(months) <= 11:
						event.log(f'В {name} нехватает каталогов. Должно быть 12.')
						continue
					if len(months) > 12:
						event.log(f'В {name} каталогов больше чем должно быть, а должно быть 12.')
						continue

					miss_month = None
					for item in months:
						miss_month = [datetime.date(year=int(name), month=month, day=1).strftime('%m %B') for month in range(1, 12, 1) if
										datetime.date(year=int(name), month=month, day=1).strftime('%m %B') not in months]
					if miss_month is not None and len(miss_month) == 0:
						event.log(f'Каталог {name} готов к архивированию. Начинаем сжатие...')
						target = os.path.join(archive_path, f'{name}.7z')
						pack(target=target, source=fullname, name=f'Отчеты за {name} год.')
						shutil.rmtree(fullname, ignore_errors=True)
					else:
						event.log(f'В {name} нехватает каталогов: {miss_month}')

			except Exception as err:
				event.log(f'Ошибка при проверке архивного каталога: {err}. Пропускаем {name}')


def pack(target: str, source: str, name: str = "root"):
	"""
	Архивирует, указанную в параметрах, папку в архив, путь к которому, также, указывается в параметрах
	:param target: полный путь и имя файла результата
	:param source: папка исходник(полный путь),
	:param name: имя корневой директории в архиве
	:return: Не возвращает параметров
	"""
	archive = py7zr.SevenZipFile(target, 'w')
	archive.writeall(source, arcname=name)
	archive.close()


if __name__ == '__main__':
	main()
