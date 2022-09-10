import dearpygui.dearpygui as gui           #pip install dearpygui
import dearpygui.demo as demo
from mysql.connector import connect, Error  #pip install mysql-connector-python
from sys import argv
import time
import csv

'''
Format of csv file
Title, Authors, Genre, Publisher
'''

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
books = None
for i in argv:
    arg = i.lower()
    if(arg == "-c"): shouldCreateDB = True
    if(arg.startswith("-file:")): books = i[len("-file:"):]
if books != None:
    try: books = open(books, "r")
    except FileNotFoundError:
        print(books, "is not a valid path")
        exit()

def openDriverAndBuff():
    log("Opening connection and command buffer")
    driver = connect(host="localhost", user=username, password=password)
    return driver, driver.cursor()
def closeDriverAndBuff():
    log("Closing connection and command buffer")
    cmdBuff.close()
    driver.close()

def Q_createDB():
    log("Creating a new database")
    cmdBuff.execute("CREATE DATABASE library")
    cmdBuff.execute("USE library")
    cmdBuff.execute('''
    CREATE TABLE books(
    name       VARCHAR(100)  NOT NULL PRIMARY KEY,
    id         INT           NOT NULL,
    available  BOOL          NOT NULL
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
    publisher  VARCHAR(20)  NOT NULL,
    b_count    INT          NOT NULL
    )
    ''')
    driver.commit()
def Q_dbContextInit():
    log("Setting up database context")
    cmdBuff.execute("USE library")
    driver.commit()
def Q_insertBookWithMeta(name, genre, authors, publisher, id, available):
    if publisher == "": publisher = "null"
    log("Inserting book:", [name, genre, authors, publisher, id])
    cmdBuff.execute("INSERT INTO books VALUES(\""+name+"\","+str(id)+","+str(available)+")")
    cmdBuff.execute("INSERT INTO bookMeta VALUES("+str(id)+",\""+genre+"\",\""+authors+"\",\""+publisher+"\",0)")
    driver.commit()
def Q_insertMember(name, id):
    log("Inserting member:", name, id)
    cmdBuff.execute("INSERT INTO members VALUES(\""+name+"\","+str(id)+")")
    driver.commit()
def Q_getHighestBookID():
    log("Getting highest book id")
    cmdBuff.execute("SELECT MAX(id) FROM books")
    result = cmdBuff.fetchall()
    driver.commit()
    id = None
    if result[0][0] == None: id = 0
    else: id = result[0][0]
    return id
def Q_getBooks():
    log("Getting all books")
    cmdBuff.execute("SELECT * FROM books")
    global books
    books = cmdBuff.fetchall()
    driver.commit()
def Q_issueBook(bookName):
    cmdBuff.execute("SELECT id FROM books WHERE name =\""+bookName+"\"")
    result = cmdBuff.fetchall()
    if result == []: return None
    cmdBuff.execute("SELECT available FROM books WHERE id ="+str(result[0][0]))
    result = cmdBuff.fetchall()
    if result[0][0] == False: return False
    driver.commit()

def GshowBooks():
    with gui.window(label="books"):
        def _name_sort_callback(sender, sort_specs):
            if sort_specs is None: return
            rows = gui.get_item_children(sender, 1)
            sortable_list = []
            for row in rows:
                first_cell = gui.get_item_children(row, 1)[0]
                sortable_list.append([row, gui.get_value(first_cell)])
            def _sorter(e): return e[1]
            sortable_list.sort(key=_sorter, reverse=sort_specs[0][1] < 0)
            new_order = []
            for pair in sortable_list: new_order.append(pair[0])
            gui.reorder_items(sender, 1, new_order)
        with gui.table(sortable=True, callback=_name_sort_callback, header_row=True, row_background=True, borders_outerH=True, borders_innerV=True, borders_outerV=True, resizable=True):
            gui.add_table_column(label="NAME")
            gui.add_table_column(label="ID", no_sort=True)
            gui.add_table_column(label="AVAILABLE", no_sort=True)
            Q_getBooks()
            for i in books:
                with gui.table_row():
                    a = "true"
                    if i[2] != True: a="false"
                    gui.add_text(i[0])
                    gui.add_text(i[1])
                    gui.add_text(a)
def Gidk():
    with gui.window(label="idk"):
        gui.add_button(label="show metrics", callback=lambda:gui.show_tool(gui.mvTool_Metrics))
        gui.add_button(label="show imgui demo", callback=lambda:demo.show_demo())

gui.create_context()
gui.create_viewport()
gui.setup_dearpygui()
gui.show_viewport()
try:
    driver, cmdBuff = openDriverAndBuff()

    if(shouldCreateDB): Q_createDB()
    else: Q_dbContextInit()
    
    hid = Q_getHighestBookID()
    
    if(books != None):
        reader = csv.reader(books)
        next(reader)
        for row in reader:
            Q_insertBookWithMeta(row[0], row[2], row[1], row[3], hid, True)
            hid += 1

    Gidk()
    GshowBooks()
    
    while gui.is_dearpygui_running(): gui.render_dearpygui_frame()
                    
except Error as e:
    print("\nMYSQL ERROR")
    print(e)
    print("username:", username)
    print("password:", password)
    exit()

closeDriverAndBuff()
gui.destroy_context()