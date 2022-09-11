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

#config.txt file has username and password for MySQL
try: f = open("config.txt", "r")
except FileNotFoundError:
    print("config.txt file not found")
    exit()

#get username and password from config.txt
username = None
password = None
minAge = None
for line in f:
    if(line[0] == '#'): continue
    if(line.startswith("username:")):
        username = line[len("username:"):].lstrip().rstrip()
    elif(line.startswith("password:")):
        password = line[len("password:"):].lstrip().rstrip()
    elif(line.startswith("min_age:")):
        minAge = int(line[len("min_age:"):].lstrip().rstrip())
f.close()

#prints the time, and then prints all the arguments passed to it
def log(*args):
    print(time.strftime("[%H:%M:%S] ", time.localtime()), end="")
    for arg in args: print(arg, end=" ")
    print()

#check if config.txt has all required fields
field = None
if(username == None): field = "username"
if(password == None): field = "password"
if(minAge == None): field = "min_age"
if(field != None):
    log(field, "has to be defined int config.txt file")
    exit()

#parse command line arguments
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

#functions to open and close connection to MySQL
def openDriverAndBuff():
    log("Opening connection and command buffer")
    driver = connect(host="localhost", user=username, password=password)
    return driver, driver.cursor()
def closeDriverAndBuff():
    log("Closing connection and command buffer")
    cmdBuff.close()
    driver.close()

hbid = None
hmid = None
#functions which execute MySQL
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
    id              INT          NOT NULL PRIMARY KEY,
    name            VARCHAR(30)  NOT NULL,
    age             INT          NOT NULL,
    prefered_genre  VARCHAR(30)  NOT NULL
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
    cmdBuff.execute('''
    CREATE TABLE reviews(
    book_id    INT     NOT NULL,
    member_id  INT     NOT NULL,
    stars      DOUBLE  NOT NULL
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
def Q_getMembers():
    log("Getting all members")
    cmdBuff.execute("SELECT name, id, age, prefered_genre FROM members")
    global members
    members = cmdBuff.fetchall()
    driver.commit()
def Q_newMember(name, id, age, preferedGenre):
    log("new member:",[name, id])
    cmdBuff.execute("INSERT INTO members VALUES("+str(id)+",\""+name+"\","+str(age)+",\""+preferedGenre.lower()+"\")")
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
def Q_removeMember(id):
    log("removing member:", id)
    cmdBuff.execute("DELETE FROM members WHERE id="+str(id))
    driver.commit()
def Q_publishReview(bookID, memberID, stars):
    log("publishing review:",[bookID, memberID, stars])
    cmdBuff.execute("INSERT INTO reviews VALUES("+str(bookID)+","+str(memberID)+","+str(stars)+")")
    driver.commit()
def Q_getStars(bookID):
    log("getting stars for bookID:", bookID)
    cmdBuff.execute("SELECT stars FROM reviews WHERE book_id="+str(bookID))
    result = cmdBuff.fetchall()
    if result == []: return None
    stars = 0
    count = 0
    for i in result:
        stars += i[0]
        count += 1
    return stars/count
def Q_getGenre(bookID):
    log("getting genre for bookID:", bookID)
    cmdBuff.execute("SELECT genre FROM bookMetas WHERE id="+str(bookID))
    result = cmdBuff.fetchall()
    driver.commit()
    return result[0][0]

#GUI
def GshowBooks():
    with gui.window(label="books"):
        def _name_sort_callback(sender, sort_specs):
            if sort_specs is None: return
            rows = gui.get_item_children(sender, 1)
            sortable_list = []
            for row in rows:
                first_cell = gui.get_item_children(row, 1)[0]
                sortable_list.append([row, gui.get_value(first_cell)])
            sortable_list.sort(reverse=sort_specs[0][1] < 0)
            new_order = []
            for pair in sortable_list: new_order.append(pair[0])
            gui.reorder_items(sender, 1, new_order)
        with gui.table(sortable=True, callback=_name_sort_callback, header_row=True, row_background=True, borders_outerH=True, borders_innerV=True, borders_outerV=True, resizable=True):
            gui.add_table_column(label="NAME")
            gui.add_table_column(label="ID", no_sort=True)
            gui.add_table_column(label="GENRE", no_sort=True)
            gui.add_table_column(label="STARS", no_sort=True)
            Q_getBooks()
            for i in books:
                id = i[1]
                with gui.table_row():
                    gui.add_text(i[0])
                    gui.add_text(i[1])
                    gui.add_text(Q_getGenre(id))
                    gui.add_text(Q_getStars(id))
def GshowMembers():
    with gui.window(label="members"):
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
            gui.add_table_column(label="AGE", no_sort=True)
            gui.add_table_column(label="PREFERED_GENRE", no_sort=True)
            Q_getMembers()
            for i in members:
                with gui.table_row():
                    gui.add_text(i[0])
                    gui.add_text(i[1])
                    gui.add_text(i[2])
                    gui.add_text(i[3])
def Gidk():
    with gui.window(label="idk"):
        gui.add_button(label="show metrics", callback=lambda:gui.show_tool(gui.mvTool_Metrics))
        gui.add_button(label="show imgui demo", callback=lambda:demo.show_demo())

#these functions get called when user clicks on a GUI button
def _setIssueData(sender, appData, userData):
    global issueMemeberID
    global issueBookID
    if userData == 0: issueMemeberID = appData
    else: issueBookID = appData
registerMemberAge = minAge
def _setRegisterData(sender, appData, userData):
    global registerMemberName
    global registerMemberAge
    global registerMemberPreferedGenre
    if userData == 0: registerMemberName = appData
    elif userData == 1: registerMemberAge = appData
    else: registerMemberPreferedGenre = appData
def _setRemoveMemberData(sender, appData, userData):
    global removeMemberID
    removeMemberID = appData
def _setReviewData(sender, appData, userData):
    global reviewBookID
    global reviewMemberID
    global reviewStars
    if userData == 0: reviewBookID = appData
    elif userData == 1: reviewMemberID = appData
    else: reviewStars = appData
def _setRegisterBookData(sender, appData, userData):
    global registerBookName
    global registerBookGenre
    global registerBookAuthors
    global registerBookPublisher
    if userData == 0: registerBookName = appData
    elif userData == 1: registerBookGenre = appData
    elif userData == 2: registerBookAuthors = appData
    else: registerBookPublisher = appData
def _issueCallback(sender, appData, userData):
    hmm = Q_issueBook(issueBookID, issueMemeberID)
    gui.set_value(userData, hmm)
def _registerMember(sender, appData, userData):
    if registerMemberName == "": return
    global hmid
    hmid += 1
    Q_newMember(registerMemberName, hmid, registerMemberAge, registerMemberPreferedGenre)
    gui.set_value(userData, "Registered new member! Your ID: "+str(hmid))
def _removeMember(sender, appData, userData):
    Q_removeMember(removeMemberID)
    gui.set_value(userData, "Removed member: "+str(removeMemberID))
def _publishReview(sender, appData, userData):
    Q_publishReview(reviewBookID, reviewMemberID, reviewStars)
    gui.set_value(userData, "Review published!")
def _registerBook(sender, appData, userData):
    global hbid
    hbid += 1
    Q_insertBookWithMeta(registerBookName, registerBookGenre, registerBookAuthors, registerBookPublisher, hbid, True)
    gui.set_value(userData, registerBookName+" is registered with ID: "+str(hbid))

#setup GUI
gui.create_context()
gui.create_viewport(title="SQLlib")
gui.setup_dearpygui()
gui.show_viewport()
with gui.font_registry(): gui.add_font("test/OpenSans.ttf", 19)
gui.bind_font(gui.last_item())

#main
try:
    driver, cmdBuff = openDriverAndBuff()

    if(shouldCreateDB): Q_createDB()
    else: Q_dbContextInit()
    
    hbid = Q_getHighestBookID()
    hmid = Q_getHighestMemberID()
    
    if(books != None):
        reader = csv.reader(books)
        next(reader)
        for row in reader:
            hbid += 1
            Q_insertBookWithMeta(row[0], row[2], row[1], row[3], hbid, True)
        books.close()

    Gidk()
    with gui.window(label="Manager", no_close=True):
        with gui.group(horizontal=True):
            gui.add_button(label="show all books", callback=GshowBooks)
            gui.add_button(label="show all members", callback=GshowMembers)
        with gui.tree_node(label="issue"):
            gui.add_input_int(label="memeber ID", callback=_setIssueData, user_data=0, min_value=0, min_clamped=True)
            gui.add_input_int(label="book ID", callback=_setIssueData, user_data=1, min_value=0, min_clamped=True)
            x = gui.add_text("")
            gui.add_button(label="issue", callback=_issueCallback, user_data=x)
        with gui.tree_node(label="New member"):
            gui.add_input_text(label="name", callback=_setRegisterData, user_data=0)
            gui.add_input_int(label="age", callback=_setRegisterData, user_data=1, min_value=minAge, min_clamped=True, default_value=minAge)
            gui.add_input_text(label="prefered genre", callback=_setRegisterData, user_data=2)
            x = gui.add_text("")
            gui.add_button(label="register", callback=_registerMember, user_data=x)
        with gui.tree_node(label="Remove member"):
            gui.add_input_int(label="id", callback=_setRemoveMemberData, min_value=0, min_clamped=True)
            x = gui.add_text("")
            gui.add_button(label="remove", callback=_removeMember, user_data=x)
        with gui.tree_node(label="Add book review"):
            gui.add_input_int(label="book id", callback=_setReviewData, user_data=0, min_value=0, min_clamped=True)
            gui.add_input_int(label="member id", callback=_setReviewData, user_data=1, min_value=0, min_clamped=True)
            gui.add_input_double(label="stars", callback=_setReviewData, user_data=2, min_value=0, max_value=5, min_clamped=True, max_clamped=True)
            x = gui.add_text("")
            gui.add_button(label="publish", callback=_publishReview, user_data=x)
        with gui.tree_node(label="Register new book"):
            gui.add_input_text(label="book name", callback=_setRegisterBookData, user_data=0)
            gui.add_input_text(label="genre", callback=_setRegisterBookData, user_data=1)
            gui.add_input_text(label="authors", callback=_setRegisterBookData, user_data=2)
            gui.add_input_text(label="publisher", callback=_setRegisterBookData, user_data=3)
            x = gui.add_text("")
            gui.add_button(label="register", callback=_registerBook, user_data=x)
    
    while gui.is_dearpygui_running(): gui.render_dearpygui_frame()
                    
except Error as e:
    print("\nMYSQL ERROR")
    print(e)
    print("username:", username)
    print("password:", password)
    exit()

#cleanup
closeDriverAndBuff()
gui.destroy_context()
