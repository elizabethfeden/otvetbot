from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler
from enum import Enum

States = Enum('States', 'TYPE TITLE CONTENT ANSWER FEEDBACK')


class MyQuestionConversationHandler:
	def __init__(self, reader, admin_id):
		self.reader = reader
		self.admin_id = admin_id

	def start(self, update, context):
		keyboard = ReplyKeyboardMarkup([['ЧГК', 'Свояк']], resize_keyboard=True)
		update.message.reply_text('Вопрос чгки или тема свояка?',
								  reply_markup=keyboard)
		return States.TYPE

	def title(self, update, context):
		typeq = (update.message.text == 'ЧГК')
		if not typeq and not update.message.text == 'Свояк':
			update.message.text(
				'Некорректный ввод! Пожалуйста, ответь с помощью встроенной '
				'клавиатуры: "ЧГК" или "Свояк".')
			return States.TYPE
		context.user_data['type'] = typeq
		update.message.reply_text(
			'Пожалуйста, укажи название вопроса.' if context.user_data['type']
			else 'Пожалуйста, укажи название темы.',
			reply_markup=ReplyKeyboardRemove())
		return States.TITLE

	def content(self, update, context):
		title = update.message.text
		if self.reader.find_title(
				title, 'chgks' if context.user_data['type'] else 'svoyaks'):
			update.message.reply_text(
				'Такое название уже занято :( Пожалуйста, введи другое.')
			return States.TITLE
		context.user_data['title'] = title
		svpattern = """
	Пожалуйста, отправь вопросы темы, пользуясь следующим шаблоном:
	10. текст вопроса

	20. текст вопроса

	30. текст вопроса

	40. текст вопроса

	50. текст вопроса
		"""
		update.message.reply_text(
			'Пожалуйста, отправь текст вопроса одним сообщением.' if
			context.user_data['type'] else svpattern)
		return States.CONTENT

	def answer(self, update, context):
		context.user_data['content'] = update.message.text
		chpattern = """
	Отправь ответ на вопрос, пользуясь следующим шаблоном:
	ОТВЕТ: тратата
	КОММЕНТАРИЙ: трутуту
		"""
		svpattern = """
	Отправь ответы и (опционально) комментарии к вопросам темы, пользуясь 
	следующим шаблоном:
	10. ответ на вопрос
	КОММЕНТАРИЙ: ляляля

	20. ответ на вопрос
	КОММЕНТАРИЙ: ляляля

	30. ответ на вопрос
	КОММЕНТАРИЙ: ляляля

	40. ответ на вопрос
	КОММЕНТАРИЙ: ляляля

	50. ответ на вопрос
	КОММЕНТАРИЙ: ляляля
		"""
		update.message.reply_text(
			chpattern if context.user_data['type'] else svpattern)
		return States.ANSWER

	def feedback(self, update, context):
		context.user_data['answer'] = update.message.text
		keyboard = ReplyKeyboardMarkup([['Да', 'Нет']], resize_keyboard=True)
		update.message.reply_text(
			'Прислать статистику по вопросу/теме? (Придет через неделю после '
			'публикации вопроса/темы на канале)',
			reply_markup=keyboard)
		return States.FEEDBACK

	def end(self, update, context):
		feedback = (update.message.text == 'Да')
		if not feedback and not update.message.text == 'Нет':
			update.message.text(
				'Некорректный ввод! Пожалуйста, ответь с помощью встроенной '
				'клавиатуры: "Да" или "Нет".')
			return States.FEEDBACK
		update.message.reply_text('Принято на рассмотрение. Огромное '
								  'спасибо!\n Что еще можно сделать? /help',
								  reply_markup=ReplyKeyboardRemove())

		answer = context.user_data['answer']
		content = context.user_data['content']
		title = context.user_data['title']
		full = f'**{title}**\n\n{content}'
		if context.user_data['type']:
			q_id = self.reader.add_question('chgks', title,
					update.message.chat_id, content, answer, feedback)
			full = f'#чгк {q_id}\n{full}'
		else:
			q_id = self.reader.add_chgk('svoyaks', title,
					update.message.chat_id, content, answer, feedback)
			full = f'#свояк {q_id}\n{full}'

		context.bot.send_message(chat_id=self.admin_id, parse_mode='Markdown',
								 text=f'Новый вопрос от [user](tg://user?id={update.message.chat_id})')
		context.bot.send_message(chat_id=self.admin_id, text=full)
		context.bot.send_message(chat_id=self.admin_id, text=answer)
		return ConversationHandler.END
