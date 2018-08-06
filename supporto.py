#---------------------QUESTO FILE CONTIENE LE FUNZIONI DI SUPPORTO-----------------------#

import requests
import datetime
import time
import json
import os

import config

#---------------------INIZIALIZZO LE VARIABILI------------------------#
URL = config.URL
CACHEFOLDER = config.CACHEFOLDER
LASTEVENTFILE = config.LASTEVENTFILE
USERSFILE = config.USERSFILE
RMUSERSFILE = config.RMUSERSFILE
HEADER = config.HEADER  


def emptyFile(file):
    if os.stat(file).st_size == 0:
        return 1
    return 0


def checkCache():
    if not os.path.isdir(config.CACHEFOLDER):
        os.makedirs(config.CACHEFOLDER)

    if not os.path.isfile(config.LASTEVENTFILE):
        f= open(config.LASTEVENTFILE,"w+").close()

    if not os.path.isfile(config.USERSFILE):
        f= open(config.USERSFILE,"w+").close()

    if not os.path.isfile(config.RMUSERSFILE):
        f= open(config.RMUSERSFILE,"w+").close()


def setLastEvent(id):
    f = open(LASTEVENTFILE, 'w')
    f.write(str(id))
    f.close()


def readLastEvent():
    if emptyFile(LASTEVENTFILE):
        return 0

    f = open(LASTEVENTFILE, 'r')
    tmp = f.read()
    f.close()
    return int(tmp)


def getChatId():
    if emptyFile(USERSFILE):
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


def addUserId(id):
    f = open(USERSFILE, 'a')
    f.write(str(id) + ";")
    f.close()


def setUserForRemove(id):
    f = open(RMUSERSFILE, 'a')
    f.write(str(id) + ";")
    f.close()

def getMaxEventId(response):
    max = 0
    for i in response['data']:
        if int(i['id']) > max:
            max = int(i['id'])
    return max


def removeUsers():
    if emptyFile(RMUSERSFILE):
        return 0

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


def prepareMessage(response, tipo):
    message = {}
    message["text"] = ""
    message["code"] = response.status_code

    if message["code"] != 200:
        message["text"] = "Errore nella richiesta HTTP (" + str(response.status_code) + ")\nIl sito potrebbe essere offline!"
        return message

    tmp = json.loads(response.text)

    message['maxid'] = getMaxEventId(tmp)

    if tipo == "evento":
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
            message['code'] = response.status_code

        if message["text"] == "":
            message["text"] = "Non ci sono News"

    else:
        if tipo == "categorylist":
            message["text"] += "Ecco le categorie disponibili:\n"

            for t in tmp['data']:
                message["text"] += t['title'].replace(" ", "-").lower() + "\n"

    return message


def RESTCall(tipo, parametro = 0):
    url = URL

    if tipo == "all":
        url += "all/" + str(parametro)

    if tipo == "latest":
        url += "latest/"

    if tipo == "category" and parametro != 0:
        url += "category/" + parametro.replace(" ", "+")

    if tipo == "categorylist":
        url += "categorylist/"

    response = requests.get(url, headers = HEADER)        

    if tipo == "categorylist":
        message = prepareMessage(response, "categorylist")
    else:
        message = prepareMessage(response, "evento")

    return message 