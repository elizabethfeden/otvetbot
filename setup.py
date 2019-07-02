"""
TODO
0 get??
..to be continued..
"""


from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
						  ConversationHandler, PicklePersistence)

#logging settings
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	level=logging.DEBUG)
logging.basicConfig(filename='log.txt', level=logging.DEBUG)
logger = logging.getLogger(__name__)

#classes
class Question:
	def __init__(self, title, text, answer, author, getstat, tried):
		self.title = title
		self.text = text
		self.answer = answer
		self.author = author
		self.getstat = getstat
		self.tried = tried

	def __eq__(self, other):
		return self.title == other.title

	def __ne__(self, other):
		return self.title != other.title

class CHGK(Question):
	def __init__(self, title, text='', answer='', author='', getstat=False, tried=0, answered=0):
		self.answered = answered
		Question.__init__(self, title, text, answer, author, getstat, tried)

class Svoyak(Question):
	def __init__(self, title, text='', answer='', author='', getstat=False, tried=0, keys=[0, 0, 0, 0, 0]):
		self.keys = keys
		Question.__init__(self, title, text, answer, author, getstat, tried)


#json serialization
import json

data = {
	'fact_id': 0,
	'chgk_id': 0,
	'chgk_publ_id': 0,
	'svoyak_id': 0,
	'svoyak_publ_id': 0,

	'fact_titles': [],
	'chgks': [],
	'svoyaks': [],
}

class QuestionEncoder(json.JSONEncoder):
		def default(self, o):
			if isinstance(o, Question):
				d = o.__dict__
				d['type_question'] = isinstance(o, CHGK)
				return d
			else: 
				return json.JSONEncoder.default(self, o)

class QuestionDecoder:
	def from_json(json_object):
		if 'type_question' in json_object:
			if json_object['type_question']:
				return CHGK(title=json_object['title'], text=json_object['text'], answer=json_object['answer'], 
					author=json_object['author'], getstat=json_object['getstat'], tried=json_object['tried'], 
					answered=json_object['answered'])
			else:
				return Svoyak(title=json_object['title'], text=json_object['text'], answer=json_object['answer'], 
					author=json_object['author'], getstat=json_object['getstat'], tried=json_object['tried'], 
					keys=json_object['keys'])
		else: 
			return json_object

def load():
	with open('data.json', 'r') as readfile:
		global data
		s = readfile.read()
		data = json.JSONDecoder(object_hook = QuestionDecoder.from_json).decode(s)

def write():
	with open('data.json', 'w') as writefile:
		s = json.dumps(data, cls=QuestionEncoder, indent=4)
		writefile.write(s)


#constants
TOKEN = ''
OWNER_ID = ''
CHANNEL_ID = '@faktikiandchgk'


#BASE COMMANDS
def start(update, context):
	text="Привет! Я - ответбот канала \"Фактики\". Ты можешь предложить мне какой-нибудь факт или чгк-вопрос," \
		" прислать обратную связь и не только! Жмакни /help, чтобы получить полный список команд."
	
	context.bot.send_message(chat_id=update.message.chat_id, text=text)


def help(update, context):
	context.bot.send_message(chat_id=update.message.chat_id, text="""
Итак, обратная связь.
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
#LOCAL COMMANDS:
#/sendtochannel message
#/mesback message {reply to forwarded message}
#/del type id
#/publish type id
#/sendstats type id
#/get type id

def cancel(update, context):
	update.message.reply_text("Команда отменена.", reply_markup = ReplyKeyboardRemove())
	return ConversationHandler.END

def error(update, context):
	logger.warning('Update "%s" caused error "%s"', update, error)

def default(update, context):
	update.message.reply_text("К сожалению, я понимаю только команды отсюда: /help")

def sendto(bot, to_id, cont):
	bot.send_message(chat_id=to_id, text=cont)

def sendch(update, context):
	if update.message.chat_id == OWNER_ID:
		sendto(context.bot, CHANNEL_ID, " ".join(context.args))

def sendstats(update, context):
	try:
		if update.message.chat_id == OWNER_ID:
			if context.args[0].lower() == 'chgk' or context.args[0].lower() == 'чгк':
				id = int(context.args[1])
				q = data['chgks'][id-1]
				percentage = int(q.answered / q.tried * 100)
				stat = "Статистика вопроса " + q.title + "\n" \
					"Ответило верно: " + str(q.answered) + "\n" \
					"Не ответило либо ответило неверно: " + str(q.tried - q.answered) + "\n" \
					"Процент ответивших: " + str(percentage) + "%"
				update.message.reply_text(stat)
				if q.author != OWNER_ID:
					sendto(context.bot, q.author, stat)
			elif context.args[0].lower() == 'svoyak' or context.args[0].lower() == 'свояк':
				id = int(context.args[1])
				q = data['svoyaks'][id-1]
				stat = "Статистика темы " +  q.title + "\n"
				for i in range(5):
				 stat += "Процент ответивших за " + str((i+1)*10) + ": " + str(int(q.keys[i] / q.tried * 100)) + "%\n"
				update.message.reply_text(stat)
				if q.author != OWNER_ID:
					sendto(context.bot, q.author, stat)
			else: 
				raise Exception
	except Exception as e:
		update.message.reply_text("Некорректный ввод" + str(e)) 

def publish(update, context):
	try:
		if update.message.chat_id == OWNER_ID:
			if context.args[0].lower() == 'chgk' or context.args[0].lower() == 'чгк':
				data['chgk_publ_id'] += 1
				update.message.reply_text("chgk_publ_id is now " + str(data['chgk_publ_id']))
			elif context.args[0].lower() == 'svoyak' or context.args[0].lower() == 'свояк':
				data['svoyak_publ_id'] += 1
				update.message.reply_text("svoyak_publ_id is now " + str(data['svoyak_publ_id']))
			else: 
				raise Exception
			write()
	except Exception as e:
		update.message.reply_text("Некорректный ввод " + str(e))


def delid(update, context):
	try:
		if update.message.chat_id == OWNER_ID:
			if context.args[0].lower() == 'fact' or context.args[0].lower() == 'факт':
				id = int(context.args[1])-1
				rem = data['fact_titles'].pop(id)
				data['fact_id'] -= 1
				update.message.reply_text("Успешно удален факт " + rem)
			elif context.args[0].lower() == 'chgk' or context.args[0].lower() == 'чгк':
				id = int(context.args[1])-1
				rem = data['chgks'].pop(id)
				data['chgk_id'] -= 1
				update.message.reply_text("Успешно удален вопрос " + str(rem.__dict__))
			elif context.args[0].lower() == 'svoyak' or context.args[0].lower() == 'свояк':
				id = int(context.args[1])-1
				rem = data['svoyaks'].pop(id)
				data['svoyak_id'] -= 1
				update.message.reply_text("Успешно удалена тема " + str(rem.__dict__))
			else: 
				raise Exception
			write()
	except Exception as e:
		update.message.reply_text("Некорректный ввод " + str(e))


#MYFACT
MF_TITLE, MF_CONTENT = range(2)

def myfact_start(update, context):
	update.message.reply_text("Пожалуйста, укажи название факта.")
	return MF_TITLE

def myfact_content(update, context):
	title = update.message.text
	if title.lower() in data['fact_titles']:
		update.message.reply_text("Такое название уже занято :( Пожалуйста, укажи другое.")
		return MF_TITLE
	context.user_data['title'] = title
	update.message.reply_text("Пожалуйста, напиши о самом факте одним сообщением.")
	return MF_CONTENT

def myfact_end(update, context):
	content = update.message.text
	title = context.user_data['title']
	content = "*" + title + "*\n\n" + content
	data['fact_id'] += 1
	data['fact_titles'].append(title.lower())
	content = "#фактик " + str(data['fact_id']) + "\n" + content
	context.bot.send_message(chat_id=OWNER_ID, parse_mode="Markdown", 
		text="Новый факт от [user](tg://user?id=" + str(update.message.chat_id) +")")
	context.bot.send_message(chat_id=OWNER_ID, parse_mode="Markdown", text=content)

	write()

	update.message.reply_text("Принято на рассмотрение. Огромное спасибо!\n" \
		"Что еще можно сделать? /help")
	return ConversationHandler.END


#MYQUESTION
MQ_TYPE, MQ_TITLE, MQ_CONTENT, MQ_ANSWER, MQ_FEEDBACK = range(5)

def mq_start(update, context):
	keyboard = ReplyKeyboardMarkup([['ЧГК', 'Свояк']], resize_keyboard = True)
	update.message.reply_text("Вопрос чгки или тема свояка?", reply_markup = keyboard)
	return MQ_TYPE

def mq_title(update, context):
	typeq = (update.message.text == 'ЧГК')
	if not typeq and not update.message.text == 'Свояк':
		update.message.text("Некорректный ввод! Пожалуйста, ответь с помощью встроенной клавиатуры: 'ЧГК' или 'Свояк'.")
		return MQ_TYPE
	context.user_data['type'] = typeq
	update.message.reply_text("Пожалуйста, укажи название вопроса." if context.user_data['type'] else "Пожалуйста, укажи название темы.", reply_markup = ReplyKeyboardRemove())
	return MQ_TITLE

def mq_content(update, context):
	title = update.message.text
	testq = CHGK(title=title.lower())
	questions = data['chgks'] if context.user_data['type'] else data['svoyaks']
	if testq in questions:
		update.message.reply_text("Такое название уже занято :( Пожалуйста, введи другое.")
		return MQ_TITLE
	context.user_data['title'] = title
	svpattern = """
Пожалуйста, отправь вопросы темы, пользуясь следующим шаблоном:
10. текст вопроса

20. текст вопроса

30. текст вопроса

40. текст вопроса

50. текст вопроса
	"""
	update.message.reply_text("Пожалуйста, отправь текст вопроса одним сообщением." if context.user_data['type'] else svpattern)
	return MQ_CONTENT

def mq_answer(update, context):
	context.user_data['content'] = update.message.text
	chpattern = """
Отправь ответ на вопрос, пользуясь следующим шаблоном:
ОТВЕТ: тратата
КОММЕНТАРИЙ: трутуту
	"""
	svpattern = """
Отправь ответы и (опционально) комментарии к вопросам темы, пользуясь следующим шаблоном:
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
	update.message.reply_text(chpattern if context.user_data['type'] else svpattern)
	return MQ_ANSWER

def mq_feedback(update, context):
	context.user_data['answer']  = update.message.text
	keyboard = ReplyKeyboardMarkup([['Да', 'Нет']], resize_keyboard = True)
	update.message.reply_text("Прислать статистику по вопросу/теме? (Придет через неделю после публикации вопроса/темы на канале)", reply_markup = keyboard)
	return MQ_FEEDBACK

def mq_end(update, context):
	feedback = (update.message.text == 'Да')
	if not feedback and not update.message.text == 'Нет':
		update.message.text("Некорректный ввод! Пожалуйста, ответь с помощью встроенной клавиатуры: 'Да' или 'Нет'.")
		return MQ_FEEDBACK
	update.message.reply_text("Принято на рассмотрение. Огромное спасибо!\n" \
		"Что еще можно сделать? /help", reply_markup = ReplyKeyboardRemove())
	
	answer = context.user_data['answer']
	question = context.user_data['content']
	full = "*" + context.user_data['title'] + "*\n\n" + question
	if context.user_data['type']:
		dataid = data['chgk_id']
		q = CHGK(title=context.user_data['title'].lower(), answer=answer, text=question, getstat=feedback, author=update.message.chat_id)
		data['chgks'].append(q)
		dataid += 1
		full = "#чгк " + str(dataid) + "\n" + full
		data['chgk_id'] = dataid
	else:
		dataid = data['svoyak_id']
		q = Svoyak(title=context.user_data['title'].lower(), answer=answer, text=question, getstat=feedback, author=update.message.chat_id)
		data['svoyaks'].append(q)
		dataid += 1
		full = "#свояк " + str(dataid) + "\n" + "Тема: " + full
		data['svoyak_id'] = dataid
	
	context.bot.send_message(chat_id=OWNER_ID, parse_mode="Markdown", 
		text="Новый вопрос от [user](tg://user?id=" + str(update.message.chat_id) +")")
	context.bot.send_message(chat_id=OWNER_ID, parse_mode="Markdown", text=full)
	context.bot.send_message(chat_id=OWNER_ID, parse_mode="Markdown", text=answer)

	write()
	return ConversationHandler.END


#ANSWERS
CHOOSING_ANS = range(1)
def vote(update, context, type, id):
	name = ('chgk_' if type else 'svoyak_') + str(id)
	context.user_data['id'] = id
	if not 'tries' in context.user_data:
		context.user_data['tries'] = []
		
	if name in context.user_data['tries']:
		return ConversationHandler.END
	else:
		context.user_data['tries'].append(name)
		if type:
			keyboard = ReplyKeyboardMarkup([['Да', 'Нет']], resize_keyboard = True)
			update.message.reply_text("Пожалуйста, ответь на анонимный вопрос (во имя статистики!)\n" \
				"Получилось ли у тебя ответить на этот вопрос?", reply_markup=keyboard)
		else:
			update.message.reply_text("Пожалуйста, ответь на анонимный вопрос (во имя статистики!)\n" \
				"Напиши номиналы вопросов, на которые у тебя получилось ответить верно, например:\n" \
				"10 40 50\n" + "Если у тебя не получилось ответить ни на один вопрос, ответь: 0")
		return CHOOSING_ANS


def anschgk(update, context):
	context.user_data['type'] = True
	questions = data['chgks']
	if len(context.args) == 0:
		id = data['chgk_publ_id']-1
		update.message.reply_text(questions[id].answer)
		return vote(update, context, True, id)
	else:
		try:
			id = int(context.args[0])
			if len(context.args) > 1:
				raise ValueError
			if id < 1 or id > data['chgk_publ_id']:
				update.message.reply_text("Неподходящий id!")
				return ConversationHandler.END
			else:
				update.message.reply_text(questions[id-1].answer)
				return vote(update, context, True, id-1)
		except ValueError:
			#int() failed, which means it's a string
			title = " ".join(context.args).lower()
			testq = CHGK(title=title)
			if testq in questions:
				id = questions.index(testq)
				update.message.reply_text(questions[id].answer)
				return vote(update, context, True, id)
			else:
				update.message.reply_text("Такого названия нет в моей базе :(")
				return ConversationHandler.END


def anssvoyak(update, context):
	context.user_data['type'] = False
	questions = data['svoyaks']
	if len(context.args) == 0:
		id = data['svoyak_publ_id']-1
		update.message.reply_text(questions[id].answer)
		return vote(update, context, False, id)
	else:
		try:
			id = int(context.args[0])
			if len(context.args) > 1:
				raise ValueError
			if id < 1 or id > data['svoyak_publ_id']:
				update.message.reply_text("Неподходящий id!")
				return ConversationHandler.END
			else:
				update.message.reply_text(questions[id-1].answer)
				return vote(update, context, False, id-1)
		except ValueError:
			#int() failed, which means it's a string
			title = " ".join(context.args).lower()
			testq = Svoyak(title=title)
			if testq in questions:
				id = questions.index(testq)
				update.message.reply_text(questions[id].answer)
				return vote(update, context, False, id)
			else:
				update.message.reply_text("Такого названия нет в моей базе :(")
				return ConversationHandler.END
	

import copy
def process_stats(update, context):
	i = context.user_data['id']
	if context.user_data['type']:
		q = data['chgks'][i]
		if update.message.text == 'Да':
			q.answered += 1
		elif not update.message.text == 'Нет':
			update.message.reply_text("Некорректный ввод! Пожалуйста, ответь с помощью встроенной клавиатуры: 'Да' или 'Нет'.")
			return CHOOSING_ANS
		q.tried += 1
		data['chgks'][i] = q
	else:
		q = copy.deepcopy(data['svoyaks'][i])
		user_keys = update.message.text.split()
		try:
			if user_keys[0] != '0':
				for key in user_keys:
					q.keys[int(int(key)/10 - 1)] += 1
			q.tried += 1
			data['svoyaks'][i] = q
		except Exception as e:
			update.message.reply_text("Некорректный ввод! " + str(e))
			return CHOOSING_ANS

	update.message.reply_text("Спасибо за участие в опросе :)", reply_markup=ReplyKeyboardRemove())
	write()
	return ConversationHandler.END


#MESSAGEME
MM_TYPING, MB_TYPING = range(2)

def messageme(update, context):
	update.message.reply_text("Пожалуйста, отправь то, что ты хочешь сказать, одним сообщением.")
	return MM_TYPING

def mm(update, context):
	context.bot.forward_message(OWNER_ID, update.message.chat_id, update.message.message_id)
	update.message.reply_text("Твое сообщение отправлено!")
	return ConversationHandler.END

def mesback(update, context):
	if update.message.chat_id == OWNER_ID:
		context.user_data['sendid'] = update.message.reply_to_message.forward_from.id
		update.message.reply_text("Ну-ка.")
		return MB_TYPING
		

def mb(update, context):
	text = "Ответ на твое сообщение в /messageme:\n\n" + update.message.text
	sendto(context.bot, context.user_data['sendid'], text)
	update.message.reply_text("Отправлено.")
	return ConversationHandler.END




#MAIN
def main():
	load()

	pp = PicklePersistence(filename='conversationbot')
	updater = Updater(token=TOKEN, persistence=pp, use_context=True)
	dp = updater.dispatcher
	dp.add_handler(CommandHandler('start', start))
	dp.add_handler(CommandHandler('help', help))
	dp.add_handler(CommandHandler('sendtochannel', sendch))
	dp.add_handler(CommandHandler('del', delid))
	dp.add_handler(CommandHandler('publish', publish))
	dp.add_handler(CommandHandler('sendstats', sendstats))

	cancelhandler = CommandHandler('cancel', cancel)

	myfact_handler = ConversationHandler(
		entry_points=[CommandHandler('myfact', myfact_start)],

		states={
			MF_TITLE: [MessageHandler(Filters.text, myfact_content)],
			MF_CONTENT: [MessageHandler(Filters.text | Filters.photo, myfact_end)]
		},

		fallbacks=[cancelhandler],
		name="myfact",
		persistent=True
	)

	myquestion_handler = ConversationHandler(
		entry_points=[CommandHandler('myquestion', mq_start)],

		states={
			MQ_TYPE: [MessageHandler(Filters.text, mq_title)],
			MQ_TITLE: [MessageHandler(Filters.text, mq_content)],
			MQ_CONTENT: [MessageHandler(Filters.text | Filters.photo, mq_answer)],
			MQ_ANSWER: [MessageHandler(Filters.text | Filters.photo, mq_feedback)],
			MQ_FEEDBACK: [MessageHandler(Filters.text, mq_end)]
		},

		fallbacks=[cancelhandler],
		name="myquestion",
		persistent=True
	)

	answerhandler = ConversationHandler(
		entry_points=[
			CommandHandler('anssvoyak', anssvoyak),
			CommandHandler('anschgk', anschgk)
		],

		states={
			CHOOSING_ANS: [MessageHandler(Filters.text, process_stats)]
		},

		fallbacks=[cancelhandler],
		name="ans",
		persistent=True
	)

	messagemehandler = ConversationHandler(
		entry_points=[
			CommandHandler('messageme', messageme),
			CommandHandler('mesback', mesback),
		],

		states={
			MM_TYPING: [MessageHandler(~Filters.command, mm)],
			MB_TYPING: [MessageHandler(~Filters.command, mb)]
		},

		fallbacks=[cancelhandler],
		name="mesme",
		persistent=True
	)

	dp.add_handler(myfact_handler)
	dp.add_handler(myquestion_handler)
	dp.add_handler(answerhandler)
	dp.add_handler(messagemehandler)
	dp.add_handler(MessageHandler(Filters.all, default))

	dp.add_error_handler(error)

	#updater.start_polling()
	
	import os
	TOKEN = os.getenv("TOKEN")
	OWNER_ID = os.getenv("OWNER_ID")
	PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
	updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TOKEN)
        updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN))

	# Run the bot until you press Ctrl-C or the process receives SIGINT,
	# SIGTERM or SIGABRT. This should be used most of the time, since
	# start_polling() is non-blocking and will stop the bot gracefully.
	updater.idle()


if __name__ == '__main__':
	main()
		
