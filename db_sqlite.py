import sqlite3

def connectDB():
    try:
        conn = sqlite3.connect('test.db')
        print("Opened database successfully")

        try:
            conn.execute('''CREATE TABLE USER
                (ID INTEGER PRIMARY KEY     AUTOINCREMENT,
                USER            TEXT    NOT NULL,
                PASSWORD        TEXT    NOT NULL
                );''')
            print("Table created successfully")
        except Exception as e:
            pass
            
        return conn
    except Exception as e:
        return "fail > %s" % e
        

def checkUser(password, conn):
    
    try:
        cursor = conn.execute("SELECT * from USER where password == '"+password+"'")
        cursor_len = len(cursor.fetchall())
        
        cursor = conn.execute("SELECT * from USER where password == '"+password+"'")
        if cursor_len > 0:
            for row in cursor:
                conn.close()
                return "The password <b>%s</b> is already used by the user: <b>%s</b>" % (row[2],row[1])
        else:
            return False
    except:
        return Exception
        
def createUser(conn,user,password):
    
    status = checkUser(password, conn)
    
    if not status:
        conn.execute("INSERT INTO USER (USER,PASSWORD) \
        VALUES ('"+user+"', "+password+")")
        conn.commit()
        conn.close()
        return "User created successfully"
    else:
        return status