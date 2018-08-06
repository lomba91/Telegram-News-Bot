#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.error import TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError
import telegram
import logging
import datetime
import time 

import supporto
import config


#---------------------INIZIALIZZO LE VARIABILI------------------------#
INGAPITOKEN = config.INGAPITOKEN
TELEGRAMTOKEN = config.TELEGRAMTOKEN
UPDATETIME = config.UPDATETIME
INITMSG = config.INITMSG
INVALIDCAT = config.INVALIDCAT
NEWSHEADER = config.NEWSHEADER
SUBSCRIBEOK = config.SUBSCRIBEOK
NOTADMINERROR = config.NOTADMINERROR


#Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


#Gestione delle eccezioni
def error(bot, update, error):
    try:
        raise error
    except Unauthorized:
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": Unauthorized: User " + update.message.chat_id + " removed")
        addUserId(update.message.chat_id) 
    except BadRequest as e:
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": Bad Request - " + str(e))
    except TimedOut as e:
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": TimedOut - " + str(e))
    except NetworkError as e:
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": NetworkError - " + str(e))
    except ChatMigrated as e:
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": ChatMigrated - " + str(e))
        addUserId(update.message.chat_id)
    except TelegramError as e:
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": TelegramError - " + str(e))



#--------------------COMANDI-----------------------#

def start(bot, update):
    bot.sendMessage(update.message.chat_id, INITMSG)


def help(bot, update):
    bot.sendMessage(update.message.chat_id, INITMSG)


#Ultime news
def ultime(bot, update):
    text = supporto.RESTCall("latest")
    bot.sendMessage(update.message.chat_id, text=NEWSHEADER)
    bot.sendMessage(update.message.chat_id, text=text['text'], parse_mode=telegram.ParseMode.HTML)


#News per categoria SISTEMARE
def filtra(bot, update, args):
    text = supporto.RESTCall("categorylist")

    cat = list()
    for t in text['text'].split('\n')[1:]:
        cat.append(t)

    try:
        if args[0].lower() in cat[:-1]:
            text = supporto.RESTCall("category", args[0].lower())
            bot.sendMessage(update.message.chat_id, text['text'], parse_mode=telegram.ParseMode.HTML)
    except:
        bot.sendMessage(update.message.chat_id, INVALIDCAT)



#Lista Categorie
def categorie(bot, update):
    text = supporto.RESTCall("categorylist")
    bot.sendMessage(update.message.chat_id, text['text'])


#Iscrizione
def iscrivi(bot, update):
    i = 0
    chatid = update.message.chat_id
    userid = update.message.from_user.id
    chat_type = bot.get_chat(chatid)
    
    if chat_type.type != "private":
        admin = bot.get_chat_administrators(chatid)
        for user_id in admin:
            if user_id.user.id != userid:
                i = i
            else:
                i = i + 1

        if i == 0:
            bot.sendMessage(update.message.chat_id, text = NOTADMINERROR)
        else:
            if supporto.findUserId(chatid) == 1:
                    msg = "Sei già iscritto!"
                    bot.sendMessage(update.message.chat_id, text=msg)
            else:
                text = supporto.RESTCall("latest")
                supporto.addUserId(chatid)
                bot.sendMessage(update.message.chat_id, text=SUBSCRIBEOK)
                bot.sendMessage(update.message.chat_id, text=text['text'], parse_mode=telegram.ParseMode.HTML)
    else:
        if supporto.findUserId(chatid) == 1:
            msg = "Sei già iscritto!"
            bot.sendMessage(update.message.chat_id, text=msg)
        else:
            text = supporto.RESTCall("latest")
            supporto.addUserId(chatid)
            bot.sendMessage(update.message.chat_id, text=SUBSCRIBEOK)
            bot.sendMessage(update.message.chat_id, text=text['text'], parse_mode=telegram.ParseMode.HTML)


#Aggiornamento automatico
def send_update(bot, update):
    id = supporto.readLastEvent()
    users = supporto.getChatId()

    if users == 0:
        return

    text = supporto.RESTCall("all", id)

    if(text['maxid'] > id):
        for u in users:
            try:
                bot.sendMessage(chat_id=u, text=text['text'], parse_mode=telegram.ParseMode.HTML)
                time.sleep(0.03)
            except Unauthorized:
                print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": Unauthorized: User " + u + " removed")
                supporto.setUserForRemove(u)

        supporto.removeUsers()
        supporto.setLastEvent(text['maxid'])
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": Update Send")        


#Avvio dei servizi
def main():

    #controllo lo stato della cache ed eventualmente la inizializzo
    supporto.checkCache()

    updater = Updater(TELEGRAMTOKEN)

    jobs = updater.job_queue
    jobs.run_repeating(send_update, UPDATETIME)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    #Registrazione dei comandi ammessi
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("iscrivi", iscrivi))
    dp.add_handler(CommandHandler("allnews", ultime))
    dp.add_handler(CommandHandler("categorie", categorie))
    dp.add_handler(CommandHandler("news", filtra, pass_args=True)) #da sistemare

    #LOG e gestione degli errori
    dp.add_error_handler(error)

    #Avvio del BOT
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()