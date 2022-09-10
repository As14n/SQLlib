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
    id         INT           NOT NULL
    )
    ''')
    cmdBuff.execute('''
    CREATE TABLE members(
    id        INT          NOT NULL PRIMARY KEY,
    name      VARCHAR(30)  NOT NULL
    )
    ''')
    cmdBuff.execute('''
    CREATE TABLE bookMetas(
    id         INT          NOT NULL PRIMARY KEY,
    genre      VARCHAR(30)  NOT NULL,
    authors    VARCHAR(30)  NOT NULL,
    publisher  VARCHAR(20)  NOT NULL,
    i_count    INT          NOT NULL
    )
    ''')
    cmdBuff.execute('''
    CREATE TABLE issues(
    book_id    INT  NOT NULL,
    member_id  INT  NOT NULL
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
    cmdBuff.execute("INSERT INTO books VALUES(\""+name+"\","+str(id)+")")
    cmdBuff.execute("INSERT INTO bookMetas VALUES("+str(id)+",\""+genre+"\",\""+authors+"\",\""+publisher+"\",0)")
    driver.commit()
def Q_getHighestBookID():
    log("Getting highest book id")
    cmdBuff.execute("SELECT MAX(id) FROM books")
    result = cmdBuff.fetchall()
    driver.commit()
    if result[0][0] == None: return 0
    return result[0][0]
def Q_getHighestMemberID():
    log("Getting highest member id")
    cmdBuff.execute("SELECT MAX(id) FROM members")
    result = cmdBuff.fetchall()
    driver.commit()
    if result[0][0] == None: return 0
    return result[0][0]
def Q_getBooks():
    log("Getting all books")
    cmdBuff.execute("SELECT name, id FROM books")
    global books
    books = cmdBuff.fetchall()
    driver.commit()
def Q_newMember(name, id):
    log("new member:",[name, id])
    cmdBuff.execute("INSERT INTO members VALUES("+str(id)+",\""+name+"\")")
    driver.commit()
def Q_issueBook(bookID, memberID):
    log("Issuing a book:",[bookID,memberID])
    bookID = str(bookID)
    memberID = str(memberID)
    cmdBuff.execute("SELECT name FROM books WHERE id ="+bookID)
    result = cmdBuff.fetchall()
    if result == []: return "Invalid book ID"
    cmdBuff.execute("SELECT member_id FROM issues WHERE book_id="+bookID)
    result = cmdBuff.fetchall()
    if result != []: return "Book has already been borrowed by member("+str(result[0][0])+")"
    cmdBuff.execute("SELECT book_id FROM issues WHERE member_id="+memberID)
    result = cmdBuff.fetchall()
    if result != []: return "Member("+memberID+") has already borrowed a book"
    cmdBuff.execute("INSERT INTO issues VALUES("+bookID+","+memberID+")")
    cmdBuff.execute("UPDATE bookMetas SET i_count = i_count + 1 WHERE id="+bookID)
    driver.commit()
    return "Issued!"

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
            Q_getBooks()
            for i in books:
                with gui.table_row():
                    gui.add_text(i[0])
                    gui.add_text(i[1])
def Gidk():
    with gui.window(label="idk"):
        gui.add_button(label="show metrics", callback=lambda:gui.show_tool(gui.mvTool_Metrics))
        gui.add_button(label="show imgui demo", callback=lambda:demo.show_demo())

def _setIssueData(sender, appData, userData):
    global issueMemeberID
    global issueBookID
    if userData == 0: issueMemeberID = appData
    else: issueBookID = appData
def _setRegisterData(sender, appData, userData):
    global registerMemberName
    registerMemberName = appData
def _issueCallback(sender, appData, userData):
    hmm = Q_issueBook(issueBookID, issueMemeberID)
    gui.set_value(userData, hmm)
def _registerMember(sender, appData, userData):
    if registerMemberName == "": return
    Q_newMember(registerMemberName, Q_getHighestMemberID()+1)
    gui.set_value(userData, "Registerd new member!")

gui.create_context()
gui.create_viewport()
gui.setup_dearpygui()
gui.show_viewport()
with gui.font_registry(): gui.add_font("test/OpenSans.ttf", 19)
gui.bind_font(gui.last_item())

try:
    driver, cmdBuff = openDriverAndBuff()

    if(shouldCreateDB): Q_createDB()
    else: Q_dbContextInit()
    
    hid = Q_getHighestBookID()
    
    if(books != None):
        reader = csv.reader(books)
        next(reader)
        for row in reader:
            hid += 1
            Q_insertBookWithMeta(row[0], row[2], row[1], row[3], hid, True)

    Gidk()
    with gui.window(label="Manager"):
        gui.add_button(label="show all books", callback=GshowBooks)
        with gui.tree_node(label="issue"):
            gui.add_input_int(label="memeber ID", callback=_setIssueData, user_data=0)
            gui.add_input_int(label="book ID", callback=_setIssueData, user_data=1)
            x = gui.add_text("")
            gui.add_button(label="issue", callback=_issueCallback, user_data=x)
        with gui.tree_node(label="New member"):
            gui.add_input_text(label="name", callback=_setRegisterData)
            x = gui.add_text("")
            gui.add_button(label="register", callback=_registerMember, user_data=x)
    
    while gui.is_dearpygui_running(): gui.render_dearpygui_frame()
                    
except Error as e:
    print("\nMYSQL ERROR")
    print(e)
    print("username:", username)
    print("password:", password)
    exit()

closeDriverAndBuff()
gui.destroy_context()
