#import dearpygui.dearpygui as dpg  #pip install dearpygui
from mysql.connector import connect, Error  #pip install mysql-connector-python
from sys import argv
import time

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
    for arg in args: print(arg, end="")
    print()

field = None
if(username == None): field = "username"
if(password == None): field = "password"
if(field != None):
    log(field, "has to be defined int config.txt file")
    exit()
    
shouldCreateDB = False
for i in argv:
    arg = i.lower()
    if(arg == "-c"): shouldCreateDB = True

def createDB(driver, cmdBuff):
    log("Creating database...")
    cmdBuff.execute("CREATE DATABASE library")
    cmdBuff.execute("USE library")
    cmdBuff.execute('''
    CREATE TABLE books(
    name VARCHAR(30) NOT NULL PRIMARY KEY,
    id   INT         NOT NULL
    )
    ''')
    cmdBuff.execute('''
    CREATE TABLE members(
    name VARCHAR(30) NOT NULL,
    id   INT         NOT NULL PRIMARY KEY
    )
    ''')
    driver.commit()
def dbContextInit(driver, cmdBuff):
    log("Setting up database context")
    cmdBuff.execute("USE library")
    driver.commit()
def insertBook(bookname, id, driver, cmdBuff):
    cmdBuff.execute("INSERT INTO books VALUES(\""+bookname+"\","+str(id)+")")
    driver.commit()

try:
    driver = connect(host="localhost", user=username, password=password)
    cmdBuff = driver.cursor()

    if(shouldCreateDB): createDB(driver, cmdBuff)
    else: dbContextInit(driver, cmdBuff)
    
    log("Closing connection...")
    cmdBuff.close()
    driver.close()
except Error as e:
    print("\nMYSQL ERROR")
    print(e)
    print("username:", username)
    print("password:", password)
