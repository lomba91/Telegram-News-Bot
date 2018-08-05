#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.error import TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError
import telegram
import logging
import requests
import datetime
import time
import json
import os


#-------------VARIABILI DI CONFIGURAZIONE--------------#
INGAPITOKEN = ""
#URL = "http://localhost/Tesi/index.php/api/Events/"
URL = "http://computer.ing.unipi.it/index.php/it/api/Events/"
CACHEFOLDER = "Cache\\"
LASTEVENTFILE = CACHEFOLDER + "lastEvent"
USERSFILE = CACHEFOLDER + "usersFile"
RMUSERSFILE = CACHEFOLDER + "rmUsersFile"
HEADER = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
            'X-Authorization': 'Bearer ' + INGAPITOKEN}
    
TELEGRAMTOKEN = ""
#UPDATETIME = 60*60*1000     #1 ora
UPDATETIME = 15     

INITMSG = "Ciao, mi occupo di tenerti aggiornato sulle news pubblicate sul sito di Ingegneria Informatica di Pisa.\n\n\
Ecco una lista di comandi che possono servirti:\n\
/start - Avvia questo Bot\n\
/help - Visualizza questo messaggio\n\
/iscrivi - Iscrive al sevizio di aggiornamento\n\
/allnews - Visualizza le news attive\n\
/news [categoria] - Visualizza le news attive della categoria indicata\n\
/categorie - Visualizza le categorie disponibili\n"


#Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
#logger = logging.getLogger(__name__)

def setLastEvent(id):
    f = open(LASTEVENTFILE, 'w')
    f.write(str(id))
    f.close()

def readLastEvent():
    if os.stat(LASTEVENTFILE).st_size == 0:
        return 0

    f = open(LASTEVENTFILE, 'r')
    tmp = f.read()
    f.close()
    return int(tmp)

def getChatId():
    if os.stat(USERSFILE).st_size == 0:
        return 0

    f = open(USERSFILE, 'r')
    lines = f.read().split(";")
    f.close()

    return lines[:-1]

def findUserId(id):
    tmp = getChatId()
    if tmp == 0:
        return 0
    else:
        for t in tmp:
            if int(t) == id:
                return 1
        return 0

def addUserId(id, file):
    f = open(file, 'a')
    f.write(str(id) + ";")
    f.close()

def getMaxEventId(c):
    tmp = json.loads(c.text)
    max = 0
    for i in tmp['data']:
        if int(i['id']) > max:
            max = int(i['id'])
    return max

def removeUsers():
    if os.stat(RMUSERSFILE).st_size == 0:
        return 

    backupFile = USERSFILE + ".backup"

    fin = open(USERSFILE, "r")
    fout = open(backupFile, "a")
    frm = open(RMUSERSFILE, "r")

    tmp = fin.read().split(";")
    rm = frm.read().split(";")

    for id in tmp[:-1]:
        for delId in rm[:-1]:
            if id != delId:
                fout.write(id + ";")
    fin.close()
    fout.close()
    frm.close()
    open(RMUSERSFILE, 'w').close()
    os.remove(USERSFILE)
    os.rename(backupFile, USERSFILE)

def prepareMessage(c):
    message = {}
    message["text"] = ""
    message["code"] = ""

    if c.status_code != 200:
        message["text"] = "Errore nella richiesta HTTP (" + str(c.status_code) + ")\nIl sito potrebbe essere offline!"
        message['code'] = c.status_code
        return message

    tmp = json.loads(c.text)

    for t in tmp['data']:
        id = t['id']
        title = "<b>" + t['title'] + "</b>"
        alias = t['alias']
        #color = t['color']
        category = t['catname']
        desc = t['shortdesc']
        date = t['startdate']
        url = "<a href='http://computer.ing.unipi.it/index.php/it/tutte/" + str(id) + "-" + alias + "'>Dettagli</a>"

        message["text"] += "<b>" + str(date) + "</b>" + "\n" + title + " - " + str(category) +"\n" + desc + "\n" + url + "\n\n"
        message['code'] = c.status_code

    if message["text"] == "":
        message["text"] = "Non ci sono News"

    return message

def ultimeNews():
    url = URL + "latest/"
    response = requests.get(url, headers = HEADER)
    message = prepareMessage(response)
    return message 

def ultimeNewsCategory(category):
    url = URL + "category/" + category.replace(" ", "+")
    response = requests.get(url, headers = HEADER)
    message = prepareMessage(response)
    return message 

def start(bot, update):
    bot.sendMessage(update.message.chat_id, INITMSG)

def help(bot, update):
    bot.sendMessage(update.message.chat_id, INITMSG)

def error(bot, update, error):
    try:
        raise error
    except Unauthorized:
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": Unauthorized: User " + update.message.chat_id + " removed")
        addUserId(update.message.chat_id, RMUSERSFILE) 
    except BadRequest as e:
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": Bad Request - " + str(e))
    except TimedOut as e:
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": TimedOut - " + str(e))
    except NetworkError as e:
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": NetworkError - " + str(e))
    except ChatMigrated as e:
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": ChatMigrated - " + str(e))
        addUserId(update.message.chat_id, RMUSERSFILE)
    except TelegramError as e:
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": TelegramError - " + str(e))


#--------------------COMANDI-----------------------#

#Ultime news
def ultime(bot, update):
    text = ultimeNews()
    if text['code'] == 200:
        bot.sendMessage(update.message.chat_id, text="Ecco le ultime News:")
        bot.sendMessage(update.message.chat_id, text=text['text'], parse_mode=telegram.ParseMode.HTML)


#News per categoria
def filtra(bot, update, args):
    url = URL + "categoryList"
    response = requests.get(url, headers = HEADER)

    tmp = json.loads(response.text)

    cat = list()
    for t in tmp['data']:
        cat.append(t['title'].lower())
    
    if args is None: #non funziona, da sistemare
        bot.sendMessage(update.message.chat_id, "Categoria non valida. /categorie per vedere quelle disponibili") 
        return  

    if args[0].replace("-", " ").lower() not in cat:
        bot.sendMessage(update.message.chat_id, "Categoria non valida. /categorie per vedere quelle disponibili")
    else:
        bot.sendMessage(update.message.chat_id, ultimeNewsCategory(args[0].replace("-", " "))['text'], parse_mode=telegram.ParseMode.HTML)

#Lista Categorie
def categorie(bot, update):
    url = URL + "categoryList"
    response = requests.get(url, headers = HEADER)
    tmp = json.loads(response.text)
    
    msg = "Ecco le categorie:\n"
    for t in tmp['data']:
        msg += t['title'].replace(" ", "-").lower() + "\n"

    bot.sendMessage(update.message.chat_id, msg)


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
            bot.sendMessage(update.message.chat_id, text = "Non sei un amministratore del gruppo e non puoi configurare il bot!")
        else:
            if findUserId(chatid) == 1:
                    msg = "Sei già iscritto!"
                    bot.sendMessage(update.message.chat_id, text=msg)
            else:
                text = ultimeNews()
                if text['code'] == 200:
                    addUserId(chatid, USERSFILE)
                bot.sendMessage(update.message.chat_id, text="Complimenti ora sei iscritto!\nQueste sono le ultime News:")
                bot.sendMessage(update.message.chat_id, text=text['text'], parse_mode=telegram.ParseMode.HTML)
    else:
        if findUserId(chatid) == 1:
            msg = "Sei già iscritto!"
            bot.sendMessage(update.message.chat_id, text=msg)
        else:
            text = ultimeNews()
            if text['code'] == 200:
                addUserId(chatid, USERSFILE)
            bot.sendMessage(update.message.chat_id, text="Complimenti ora sei iscritto!\nQueste sono le ultime News:")
            bot.sendMessage(update.message.chat_id, text=text['text'], parse_mode=telegram.ParseMode.HTML)


#Aggiornamento automatico
def send_update(bot, update):
    id = readLastEvent()

    url = URL
    url += "all/" + str(id)
    response = requests.get(url, headers = HEADER)

    max = getMaxEventId(response)

    if(max > id):
        text = prepareMessage(response)
        users = getChatId()

        if text['code'] == 200:
            for u in users:
                try:
                    bot.sendMessage(chat_id=u, text=text['text'], parse_mode=telegram.ParseMode.HTML)
                    time.sleep(0.03)
                except Unauthorized:
                    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": Unauthorized: User " + u + " removed")
                    addUserId(u, RMUSERSFILE) 

            removeUsers()
            setLastEvent(max)
            print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": Aggiornamento Inviato")        


#Avvio dei servizi
def main():
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
