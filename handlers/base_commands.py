from telegram import ReplyKeyboardRemove
from telegram.ext import ConversationHandler
import logging


def default(update, context):
	update.message.reply_text(
		'К сожалению, я понимаю только команды отсюда: /help')


class BaseCommandsHandler:
	def __init__(self):
		self.logger = logging.getLogger(__name__)

	def start(self, update, context):
		update.message.reply_text('Привет! Я - ответбот канала "Фактики".'
			'Ты можешь предложить мне какой-нибудь факт '
			'или чгк-вопрос, ''прислать обратную связь и не только! '
			'Жмакни /help, чтобы получить полный список команд.')

	def help(self, update, context):
		context.bot.send_message(chat_id=update.message.chat_id,
								 text="""
Обратная связь:
/messageme - замечания, предложения, общение

Предложить свое:
/myfact - предложить факт на канал
/myquestion - предложить чгк-вопрос или тему свояка на канал

Ответить на вопрос или свояк:
/anschgk - получить ответ на последний вопрос, запощенный на канале
/anschgk id - получить ответ на вопрос номер id (число)
/anschgk name - получить ответ на вопрос под заголовком 'name'
/anssvoyak - получить ответы на последнюю тему свояка, запощенную на канале
/anssvoyak id - получить ответы на тему свояка номер id (число)
/anssvoyak name - получить ответы на тему свояка под названием 'name'

/cancel - отменить выполнение текущей команды
		""")

	def cancel(self, update, context):
		update.message.reply_text('Команда отменена.',
								reply_markup=ReplyKeyboardRemove())
		return ConversationHandler.END

	def error(self, update, context):
		self.logger.warning('Update "%s" caused error "%s"', update,
							logging.error)
