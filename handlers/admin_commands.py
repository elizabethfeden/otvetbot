from telegram.ext import ConversationHandler
from enum import Enum

"""
	LIST OF ADMIN COMMANDS
	/sendtochannel message
	/del type id
	/publish type id
	/sendstats type id
	/get type id
	/settitle type id
"""

Question = Enum('Question', 'FACT CHGK SVOYAK')


def get_type(t_name):
	name = t_name.lower()
	if name == 'fact' or name == 'факт':
		return Question.FACT
	if name == 'chgk' or name == 'чгк':
		return Question.CHGK
	if name == 'svoyak' or name == 'свояк':
		return Question.SVOYAK


class AdminCommandsHandler:
	def __init__(self, admin_id, channel_id, reader):
		self.admin_id = int(admin_id)
		self.channel_id = channel_id
		self.reader = reader

	def sendch(self, update, context):
		if update.message.chat_id == self.admin_id:
			context.bot.send_message(chat_id=self.channel_id,
									 text=' '.join(context.args))

	def getq(self, update, context):
		try:
			if update.message.chat_id == self.admin_id:
				if get_type(context.args[0]) == Question.CHGK:
					q_id = int(context.args[1])
					publ_id, title, text = \
						self.reader.prepare_question_for_publication(q_id,
																	 'chgks')
					update.message.reply_text(
						f'#чгк {publ_id}\n{title}\n\n{text}')
				elif get_type(context.args[0]) == Question.SVOYAK:
					q_id = int(context.args[1])
					publ_id, title, text = \
						self.reader.prepare_question_for_publication(q_id,
																	 'svoyaks')
					update.message.reply_text(
						f'#свояк {publ_id}\n{title}\n\n{text}')
				else:
					raise Exception
		except Exception as e:
			update.message.reply_text('Некорректный ввод: ' + str(e))

	def sendstats(self, update, context):
		try:
			if update.message.chat_id == self.admin_id:
				q_id = int(context.args[1])
				if get_type(context.args[0]) == Question.CHGK:
					question_data = self.reader.get_question_data(q_id,
																  'chgks')
					percentage = int(question_data[9] / question_data[8] * 100)
					stat = f'Статистика вопроса {question_data[3]}\n' \
						   f'Ответило верно: {question_data[9]}\n' \
						   f'Ответило неверно: ' \
						   f'{question_data[8] - question_data[9]}\n' \
						   f'Процент ответивших: {percentage}%'
				elif get_type(context.args[0]) == Question.SVOYAK:
					question_data = self.reader.get_question_data(q_id,
																  'svoyaks')
					stat = f'Статистика темы {question_data[3]}\n'
					for i, key in enumerate(question_data[9]):
						stat += f'Процент ответивших за {(i + 1) * 10}: ' \
								f'{int(key / question_data[8] * 100)}%\n'
				else:
					raise Exception(
						'Ожидается первый аргумент "свояк" или "чгк"')

				update.message.reply_text(stat)
				if int(question_data[2]) != self.admin_id and question_data[7]:
					context.bot.send_message(chat_id=question_data[2],
											 text=stat)
		except Exception as e:
			update.message.reply_text('Некорректный ввод: ' + str(e))

	def publish(self, update, context):
		try:
			if update.message.chat_id == self.admin_id:
				if get_type(context.args[0]) == Question.CHGK:
					self.reader.publish_new_question('chgks')
				elif get_type(context.args[0]) == Question.SVOYAK:
					self.reader.publish_new_question('svoyaks')
				else:
					raise Exception

				update.message.reply_text('Успешно опубликовано.')
		except Exception as e:
			update.message.reply_text('Некорректный ввод: ' + str(e))

	def delid(self, update, context):
		try:
			if update.message.chat_id == self.admin_id:
				q_id = int(context.args[1])
				if get_type(context.args[0]) == Question.FACT:
					rem = self.reader.delete_row(q_id, 'facts')
				elif get_type(context.args[0]) == Question.CHGK:
					rem = self.reader.delete_row(q_id, 'chgks')
				elif get_type(context.args[0]) == Question.SVOYAK:
					rem = self.reader.delete_row(q_id, 'chgks')
				else:
					raise Exception

				update.message.reply_text('Успешно удалено: ' + rem)
		except Exception as e:
			update.message.reply_text('Некорректный ввод: ' + str(e))

	def set_title_start(self, update, context):
		try:
			if update.message.chat_id == self.admin_id:
				context.user_data['id'] = int(context.args[1])
				if get_type(context.args[0]) == Question.CHGK:
					context.user_data['table_name'] = 'chgks'
				elif get_type(context.args[0]) == Question.SVOYAK:
					context.user_data['table_name'] = 'svoyaks'
				else:
					raise Exception
				update.message.reply_text('Новое название:')
				return 0
			else:
				return ConversationHandler.END
		except Exception as e:
			update.message.reply_text('Некорректный ввод: ' + str(e))
			return ConversationHandler.END

	def set_title_end(self, update, context):
		title = update.message.text.lower()
		if self.reader.find_title(title, context.user_data['table_name']):
			update.message.reply_text('Такое название уже занято! Дай другое.')
			return 0
		self.reader.set_title(context.user_data['id'], title,
							  context.user_data['table_name'])
		update.message.reply_text('Обновлено.')
		return ConversationHandler.END
