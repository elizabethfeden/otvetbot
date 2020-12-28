from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler


class AnswerQuestionConversationHandler:
	def __init__(self, reader, admin_id):
		self.reader = reader
		self.admin_id = admin_id

	def vote(self, update, context, q_type, q_id):
		name = ('chgk_' if q_type else 'svoyak_') + str(q_id)
		context.user_data['id'] = q_id

		# one user may not vote multiple times
		if 'tries' not in context.user_data:
			context.user_data['tries'] = []

		if name in context.user_data['tries']:
			return ConversationHandler.END
		else:
			if q_type:
				keyboard = ReplyKeyboardMarkup([['Да', 'Нет']],
											   resize_keyboard=True)
				update.message.reply_text(
					'Пожалуйста, ответь на анонимный вопрос (во имя '
					'статистики!)\nПолучилось ли у тебя ответить на этот вопрос?',
					reply_markup=keyboard)
			else:
				update.message.reply_text(
					'Пожалуйста, ответь на анонимный вопрос (во имя '
					'статистики!)\nНапиши номиналы вопросов, на которые у '
					'тебя получилось ответить верно, например:\n10 40 50\n'
					'Если у тебя не получилось ответить ни на один вопрос, ответь: 0')
			context.user_data['tries'].append(name)
			return 0

	def process_input(self, update, context, q_type):
		context.user_data['type'] = q_type
		table_name = 'chgks' if q_type else 'svoyaks'
		try:
			if len(context.args) == 0:
				q_id = self.reader.get_last_publ_id(table_name)
			elif len(context.args) == 1:
				q_id = int(context.args[0])
			else:
				raise ValueError

			if q_id < 1 or q_id > self.reader.get_last_publ_id(table_name):
				update.message.reply_text('Неподходящий id!')
				return ConversationHandler.END
		except ValueError:
			# int() failed, which means it's context.args where a string
			title = ' '.join(context.args).lower()
			q_id = self.reader.get_id_by_title(title, table_name)
			if q_id is None:
				update.message.reply_text('Такого названия нет в моей базе :(')
				return ConversationHandler.END

		update.message.reply_text(self.reader.get_answer_by_id(q_id, table_name))
		return self.vote(update, context, q_type, q_id)

	def anschgk(self, update, context):
		return self.process_input(update, context, True)

	def anssvoyak(self, update, context):
		return self.process_input(update, context, False)

	def process_stats(self, update, context):
		q_id = context.user_data['id']
		if context.user_data['type']:
			if update.message.text != 'Нет' and update.message.text != 'Да':
				update.message.reply_text(
					'Некорректный ввод! Пожалуйста, ответь с помощью встроенной'
					'клавиатуры: "Да" или "Нет".')
				return 0
			self.reader.update_chgk_stats(q_id, int(update.message.text == 'Да'))
		else:
			deltas = [0] * 5
			user_keys = update.message.text.split()
			if user_keys[0] != '0':
				for key in user_keys:
					if key not in ('10', '20', '30', '40', '50'):
						update.message.reply_text('Некорректный ввод!')
						return 0
					deltas[int(int(key) / 10 - 1)] = 1
			self.reader.update_svoyak_stats(q_id, deltas)

		update.message.reply_text('Спасибо за участие в опросе :)',
								  reply_markup=ReplyKeyboardRemove())
		return ConversationHandler.END
