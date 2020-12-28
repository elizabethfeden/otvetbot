import logging
import os

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, \
	ConversationHandler

import databases
from handlers import base_commands, admin_commands, myfact_conversation, \
	myquestion_conversation, ansquestion_conversation, feedback_conversation

# ======= LOGGING SETTINGS =======

logging.basicConfig(
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	level=logging.DEBUG)
logging.basicConfig(filename='log.txt', level=logging.DEBUG)

# ======= CONSTANTS AND DATA =======

reader = databases.DatabaseReader(os.getenv("DATABASE_URL"))

TOKEN = os.getenv('TOKEN')
OWNER_ID = os.getenv('OWNER_ID')
CHANNEL_ID = '@faktikiandchgk'


# ======= BASE COMMANDS =======

def init_base_commands(dispatcher):
	bch = base_commands.BaseCommandsHandler()
	dispatcher.add_handler(CommandHandler('start', bch.start))
	dispatcher.add_handler(CommandHandler('help', bch.help))
	dispatcher.add_handler(MessageHandler(Filters.all, bch.default))
	dispatcher.add_error_handler(bch.error)
	return CommandHandler('cancel', bch.cancel)


# ======= ADMIN COMMANDS =======

def init_admin_commands(dispatcher, cancel_handler):
	ach = admin_commands.AdminCommandsHandler(OWNER_ID, CHANNEL_ID, reader)
	dispatcher.add_handler(CommandHandler('sendtochannel', ach.sendch))
	dispatcher.add_handler(CommandHandler('del', ach.delid))
	dispatcher.add_handler(CommandHandler('publish', ach.publish))
	dispatcher.add_handler(CommandHandler('sendstats', ach.sendstats))
	dispatcher.add_handler(CommandHandler('get', ach.getq))
	dispatcher.add_handler(ConversationHandler(
		entry_points=[CommandHandler('settitle', ach.set_title_start)],

		states={
			0: [MessageHandler(Filters.text, ach.set_title_end)],
		},

		fallbacks=[cancel_handler]
	))


# ======= MYFACT CONVERSATION =======

def init_myfact_conversation(dispatcher, cancel_handler):
	mfc = myfact_conversation.MyFactConversationHandler(reader, OWNER_ID)
	States = myfact_conversation.States
	dispatcher.add_handler(ConversationHandler(
		entry_points=[CommandHandler('myfact', mfc.start)],

		states={
			States.TITLE: [MessageHandler(Filters.text, mfc.content)],
			States.CONTENT: [
				MessageHandler(Filters.text | Filters.photo, mfc.end)]
		},

		fallbacks=[cancel_handler]
	))


# ======= MYQUESTION CONVERSATION =======

def init_myquestion_conversation(dispatcher, cancel_handler):
	mqc = myquestion_conversation.MyQuestionConversationHandler(reader, OWNER_ID)
	States = myfact_conversation.States
	dispatcher.add_handler(ConversationHandler(
		entry_points=[CommandHandler('myquestion', mqc.start)],

		states={
			States.TYPE: [MessageHandler(Filters.text, mqc.title)],
			States.TITLE: [MessageHandler(Filters.text | Filters.photo,
										  mqc.content)],
			States.CONTENT: [
				MessageHandler(Filters.text | Filters.photo, mqc.answer)],
			States.ANSWER: [
				MessageHandler(Filters.text | Filters.photo, mqc.feedback)],
			States.FEEDBACK: [MessageHandler(Filters.text, mqc.end)]
		},

		fallbacks=[cancel_handler]
	))


# ======= ANSWERS CONVERSATION =======

def init_ansquestion_conversation(dispatcher, cancel_handler):
	aqc = ansquestion_conversation.AnswerQuestionConversationHandler(reader,
																	 OWNER_ID)
	dispatcher.add_handler(ConversationHandler(
		entry_points=[
			CommandHandler('anssvoyak', aqc.anssvoyak),
			CommandHandler('anschgk', aqc.anschgk)
		],

		states={
			0: [MessageHandler(Filters.text, aqc.process_stats)]
		},

		fallbacks=[cancel_handler]
	))


# ======= FEEDBACK CONVERSATIONS =======

def init_feedback_conversations(dispatcher, cancel_handler):
	fch = feedback_conversation.FeedbackConversationHandler(OWNER_ID)
	Typing = feedback_conversation.Typing
	dispatcher.add_handler(ConversationHandler(
		entry_points=[
			CommandHandler('messageme', fch.message_me_start),
			CommandHandler('mesback', fch.message_back_start),
			CommandHandler('mesto', fch.message_to),
		],

		states={
			Typing.USER: [MessageHandler(~Filters.command, fch.message_me_end)],
			Typing.ADMIN: [MessageHandler(~Filters.command,
										  fch.message_back_end)]
		},

		fallbacks=[cancel_handler]
	))


def main():
	updater = Updater(token=TOKEN, use_context=True)
	dispatcher = updater.dispatcher

	cancel_handler = init_base_commands(dispatcher)
	init_admin_commands(dispatcher, cancel_handler)
	init_myfact_conversation(dispatcher, cancel_handler)
	init_myquestion_conversation(dispatcher, cancel_handler)
	init_ansquestion_conversation(dispatcher, cancel_handler)
	init_feedback_conversations(dispatcher, cancel_handler)

	app_name = os.environ.get('HEROKU_APP_NAME')
	updater.start_webhook(listen='0.0.0.0',
						  port=int(os.environ.get('PORT', '8443')),
						  url_path=TOKEN)
	updater.bot.set_webhook(f'https://{app_name}.herokuapp.com/{TOKEN}')
	updater.idle()


if __name__ == '__main__':
	main()
