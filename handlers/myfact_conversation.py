from telegram.ext import ConversationHandler
from enum import Enum

States = Enum('States', 'TITLE CONTENT')


class MyFactConversationHandler:
	def __init__(self, reader, admin_id):
		self.reader = reader
		self.admin_id = admin_id

	def start(self, update, context):
		update.message.reply_text("Пожалуйста, укажи название факта.")
		return States.TITLE

	def content(self, update, context):
		title = update.message.text
		if self.reader.find_title(title, 'facts'):
			update.message.reply_text(
				'Такое название уже занято :( Пожалуйста, укажи другое.')
			return States.TITLE
		context.user_data['title'] = title
		update.message.reply_text(
			'Пожалуйста, напиши о самом факте одним сообщением.')
		return States.CONTENT

	def end(self, update, context):
		content = update.message.text
		title = context.user_data['title']
		content = f'**{title}**\n\n{content}'
		f_id = self.reader.add_fact(title)
		content = f'#фактик {f_id}\n{content}'
		context.bot.send_message(chat_id=self.admin_id, parse_mode='Markdown',
								 text=f'Новый факт от [user](tg://user?id='
									  f'{update.message.chat_id})')
		context.bot.send_message(chat_id=self.admin_id, text=content)

		update.message.reply_text('Принято на рассмотрение. Огромное '
								  'спасибо!\n Что еще можно сделать? /help')
		return ConversationHandler.END
