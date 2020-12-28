from telegram.ext import ConversationHandler
from enum import Enum

Typing = Enum('States', 'USER ADMIN')


class FeedbackConversationHandler:
	def __init__(self, admin_id):
		self.admin_id = admin_id

	def message_me_start(self, update, context):
		update.message.reply_text(
			'Пожалуйста, отправь то, что ты хочешь сказать, одним сообщением.')
		return Typing.USER

	def message_me_end(self, update, context):
		context.bot.send_message(self.admin_id, str(update.message.chat_id))
		context.bot.forward_message(self.admin_id, update.message.chat_id,
									update.message.message_id)
		update.message.reply_text('Твое сообщение отправлено!')
		return ConversationHandler.END

	def message_back_start(self, update, context):
		if update.message.chat_id == self.admin_id:
			context.user_data['send_id'] = update.message.reply_to_message.text
			update.message.reply_text('Ну-ка.')
			return Typing.ADMIN
		else:
			return ConversationHandler.END

	def message_back_end(self, update, context):
		context.bot.send_message(context.user_data['send_id'],
								 update.message.text)
		update.message.reply_text('Отправлено.')
		return ConversationHandler.END

	def message_to(self, update, context):
		if update.message.chat_id == self.admin_id:
			context.user_data['send_id'] = context.args[0]
			update.message.reply_text('Ну-ка.')
			return Typing.ADMIN
		else:
			return ConversationHandler.END