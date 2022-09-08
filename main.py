#import dearpygui.dearpygui as dpg  #pip install dearpygui
from mysql.connector import connect, Error  #pip install mysql-connector-python
from sys import argv
import time
import csv

try: f = open("config.txt", "r")
except FileNotFoundError:
    print("config.txt file not found")
    exit()
    
username = None
password = None
for line in f:
    if(line[0] == '#'): continue
    if(line.startswith("username:")):
        username = line[len("username:"):].lstrip().rstrip()
    elif(line.startswith("password:")):
        password = line[len("password:"):].lstrip().rstrip()

def log(*args):
    print(time.strftime("[%H:%M:%S] ", time.localtime()), end="")
    for arg in args: print(arg, end=" ")
    print()

field = None
if(username == None): field = "username"
if(password == None): field = "password"
if(field != None):
    log(field, "has to be defined int config.txt file")
    exit()
    
shouldCreateDB = False
bookFile = None
for i in argv:
    arg = i.lower()
    if(arg == "-c"): shouldCreateDB = True
    if(arg.startswith("-file:")): bookFile = i[len("-file:"):]

def openDriverAndBuff():
    log("Opening connection and command buffer")
    driver = connect(host="localhost", user=username, password=password)
    return driver, driver.cursor()
def closeDriverAndBuff(driver, cmdBuff):
    log("Closing connection and command buffer")
    cmdBuff.close()
    driver.close()
def Q_createDB(driver, cmdBuff):
    log("Creating a new database")
    cmdBuff.execute("CREATE DATABASE library")
    cmdBuff.execute("USE library")
    cmdBuff.execute('''
    CREATE TABLE books(
    name  VARCHAR(100)  NOT NULL PRIMARY KEY,
    id    INT           NOT NULL
    )
    ''')
    cmdBuff.execute('''
    CREATE TABLE members(
    id    INT          NOT NULL PRIMARY KEY,
    name  VARCHAR(30)  NOT NULL
    )
    ''')
    cmdBuff.execute('''
    CREATE TABLE bookMeta(
    id         INT          NOT NULL PRIMARY KEY,
    genre      VARCHAR(30)  NOT NULL,
    authors    VARCHAR(30)  NOT NULL,
    publisher  VARCHAR(20)
    )
    ''')
    driver.commit()
def Q_dbContextInit(driver, cmdBuff):
    log("Setting up database context")
    cmdBuff.execute("USE library")
    driver.commit()
def Q_insertBook(name, id, genre, authors, publisher, driver, cmdBuff):
    if publisher == "": publisher = "null"
    log("Inserting book:", [name, id, genre, authors, publisher])
    cmdBuff.execute("INSERT INTO books VALUES(\""+name+"\","+str(id)+")")
    cmdBuff.execute("INSERT INTO bookMeta VALUES("+str(id)+",\""+genre+"\",\""+authors+"\",\""+publisher+"\")")
    driver.commit()
def Q_insertMember(name, id, driver, cmdBuff):
    log("Inserting member:", name, id)
    cmdBuff.execute("INSERT INTO members VALUES(\""+name+"\","+str(id)+")")
    driver.commit()
def Q_getHighestBookID(driver, cmdBuff):
    log("Getting highest book id")
    cmdBuff.execute("SELECT MAX(id) FROM books")
    result = cmdBuff.fetchall()
    driver.commit()
    id = None
    if result[0][0] == None: id = 0
    else: id = result[0][0]
    return id

try:
    driver, cmdBuff = openDriverAndBuff()

    if(shouldCreateDB): Q_createDB(driver, cmdBuff)
    else: Q_dbContextInit(driver, cmdBuff)
    
    hid = Q_getHighestBookID(driver, cmdBuff)
    
    if(bookFile != None):
        books = open(bookFile, "r")
        reader = csv.reader(books)
        next(reader)
        for row in reader:
            genre = row[3]
            if row[1] == "": continue
            if genre  == "": genre = row[2]
            Q_insertBook(row[0], hid, genre, row[1], row[5], driver, cmdBuff)
            hid += 1
   
    closeDriverAndBuff(driver, cmdBuff)
except Error as e:
    print("\nMYSQL ERROR")
    print(e)
    print("username:", username)
    print("password:", password)
