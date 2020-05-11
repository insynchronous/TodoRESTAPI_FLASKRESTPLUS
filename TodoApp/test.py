''' As per rule of the task started the task form the documentation starter code '''

from flask import Flask, request, session
from flask_restplus import Api, Resource, fields
from werkzeug.contrib.fixers import ProxyFix
import sqlite3
from functools import wraps



# Date converter
import datetime

def datestdtojd (stddate):
    fmt= r'%d-%m-%Y'
    sdtdate = datetime.datetime.strptime(stddate, fmt)
    entered_year = sdtdate.year
    sdtdate = sdtdate.timetuple()
    jdate = str(sdtdate.tm_yday)
    if len(jdate) < 3:
        jdate = str("0")+ jdate
    return(str(entered_year)+jdate)

def jdtodatestd (jdate):
    fmt = '%Y%j'
    datestd = datetime.datetime.strptime(jdate, fmt).date()
    datestd = datestd.strftime(r"%d-%m-%Y")
    return(datestd)

# print(datestdtojd('12-12-2000'))
# print(jdtodatestd("2000347"))


# Date converter ends


# Decorators

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session:
            current_user = [session['username'], session['isadmin']]
            return func( *args, **kwargs)
        else:
            return {"Error":"Authentication required"}
    return wrapper

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session['isadmin'] == "True":
            return func(*args, **kwargs)
        else:
            return {"Error":"Administrator privilages required"}
    return wrapper


# Decorators Ends



# Database Querries


insert_db = "INSERT INTO TODO('task','due_date','status') VALUES (?,?,?)"
get_todo_by_id = "SELECT * FROM TODO WHERE id = {}"
get_todo_all = "SELECT * FROM TODO"
update_todo = "UPDATE TODO SET task = '{}', due_date = '{}', status = '{}' WHERE id = {}"
delete_todo = "DELETE FROM TODO WHERE id = {}"
update_todo_status = "UPDATE TODO SET status = '{}' WHERE id = {}"
get_finished_todo = "SELECT * FROM TODO WHERE status = 'Finished'"
get_over_due_todo = 'SELECT * FROM TODO WHERE due_date < {} AND status != "Finished" '
get_todo_date = "SELECT * FROM TODO WHERE due_date = {}"

insert_db_user = "INSERT INTO USERS('username','password','isadmin') VALUES (?,?,?)"
delete_user = "DELETE FROM USERS WHERE id = {}"
find_username = "SELECT * FROM USERS WHERE username = '{}'"


# Database Querries Ends




app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(app, title='TodoMVC API',
    description='A simple TodoMVC API for programming-test',)
app.secret_key = 'TESTKEY'
ns = api.namespace('todos', description='TODO operations')



todo = api.model('Todo', {
    'id': fields.Integer(readonly=True, description='The task unique identifier'),
    'task': fields.String(required=True, description='The task details'),
    'due_date': fields.String(required = True, description='The due date'),
    'status': fields.String(required = True, description='Status of the task'),
})

user = api.model('users',
{
    'id': fields.Integer(readonly=True, description='Users unique identifier'),
    'username': fields.String(required=True, description='Username for user'),
    'password': fields.String(required=True, description='Password for user'),
    'isadmin': fields.String(required=True, description='Password for user'),

}
)


class TodoDAO(object):
    # def __init__(self):
        # self.counter = 0
        # self.todos = []

    def get(self, id):
        
        try:
            with sqlite3.connect('todo_db.db') as conn:
                crsr = conn.cursor()
                res = crsr.execute(get_todo_by_id.format(id)).fetchall()
                return {'id':res[0][0], 'task' :res[0][1], 'due_date': jdtodatestd(str(res[0][2])) , 'status':res[0][3] }     
        # for todo in self.todos:
        #     if todo['id'] == id:
        #         return todo
        except:
            api.abort(404, "Todo {} doesn't exist".format(id))

    def create(self, data):

        try:
            with sqlite3.connect('todo_db.db') as conn:
                crsr = conn.cursor()
                # todo = data
                # todo['id'] = self.counter = self.counter + 1
                crsr.execute(insert_db,(data['task'],int(datestdtojd(data['due_date'])),data['status'] ))
                conn.commit()
                return {"Success":"Todo Created"}, 201
        except:
            return {"Failure":"Todo not created"}
            # self.todos.append(todo)
            # return todo

    def update(self, id, data):
        try:
            with sqlite3.connect('todo_db.db') as conn:
                crsr = conn.cursor()
                crsr.execute(update_todo.format(data['task'],data['due_date'], data['status'], id))
                res = crsr.execute(get_todo_by_id.format(id)).fetchall()
                return {'id':res[0][0], 'task' :res[0][1], 'due_date': jdtodatestd(str(res[0][2])) , 'status':res[0][3] } 
        except :
            return {"Failure":"Error"}, 304

        # todo = self.get(id)
        # todo.update(data)
        # return todo

    def delete(self, id):

        try:
            with sqlite3.connect('todo_db.db') as conn:
                crsr = conn.cursor()
                crsr.execute(delete_todo.format(id))
                return  {"Success":"Todo Deleted"}
        except:
            return {"Failure":"Error"}, 404


        # todo = self.get(id)
        # self.todos.remove(todo)


DAO = TodoDAO()



@ns.route('/')
class TodoList(Resource):
    '''Shows a list of all todos, and lets you POST to add new tasks'''
    @login_required
    @ns.doc('list_todos')
    @ns.marshal_list_with(todo)
    def get(self):
        '''List all tasks'''
        with sqlite3.connect('todo_db.db') as conn:
            try:
                crsr = conn.cursor()
                all_todo = crsr.execute(get_todo_all).fetchall()
                todo_array = []
                for i in range(0, len(all_todo)):
                    todo_array.append({'id':all_todo[i][0], 
                    'task' :all_todo[i][1],
                    'due_date': jdtodatestd(str(all_todo[0][2])) , 
                    'status':all_todo[i][3] } )
                return todo_array

            except:
                api.abort(500, " Something went wrong ")
        
    @login_required
    @admin_required
    @ns.doc('create_todo')
    @ns.expect(todo)
    def post(self):
        '''Create a new task'''
        return DAO.create(api.payload)


@ns.route('/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')
class Todo(Resource):
    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_todo')
    @ns.marshal_with(todo)
    @login_required
    def get(self, id):
        '''Fetch a given resource'''
        return DAO.get(id)

    @login_required
    @admin_required
    @ns.doc('delete_todo')
    @ns.response(204, 'Todo deleted')
    def delete(self, id):
        '''Delete a task given its identifier'''
        DAO.delete(id)

    @login_required
    @admin_required
    @ns.expect(todo)
    @ns.marshal_with(todo)
    def put(self, id):
        '''Update a task given its identifier'''
        return DAO.update(id, api.payload)


@ns.route('/updatestatus/<int:id>/<statusupdate>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')
@ns.param('statusupdate', 'Set status: Finished/UnderConst/Start')
class TodoUpdate(Resource):

    @login_required
    @admin_required
    @ns.response(200, 'Status updated')
    def put(self,id,statusupdate):
        print(statusupdate)
        try:
            with sqlite3.connect('todo_db.db') as conn:
                crsr = conn.cursor()
                crsr.execute(update_todo_status.format(statusupdate,id))
                conn.commit()
                return {"Success":"Status updated"},200
        except:
            return {"Failure":"Todo not found"},404

        
@ns.route('/ﬁnished')
@ns.response(404, 'No todos found')
class TodoFinished(Resource):

    @login_required
    @ns.doc('Finished Todos')
    @ns.marshal_list_with(todo)
    @ns.response(200, 'Success')
    def get(self):
        try:
            with sqlite3.connect('todo_db.db') as conn:
                crsr = conn.cursor()
                res = crsr.execute(get_finished_todo).fetchall()
                if res:
                    todo_array = []
                    for i in range(0, len(res)):
                        todo_array.append({'id':res[i][0], 
                        'task' :res[i][1],
                        'due_date': jdtodatestd(str(res[0][2])) , 
                        'status':res[i][3] } )
                    return todo_array
                else:
                    return "", 404
        except:
            return {"Failure":" Cannot access "}, 404


@ns.route('/overdue')
@ns.response(404, 'No todos found')
class overdue(Resource):

    @login_required
    def get(self):
        from datetime import date
        today = date.today()
        today_date = today.strftime(r"%d-%m-%Y")
        try:
            with sqlite3.connect('todo_db.db') as conn:
                crsr = conn.cursor()
                res = crsr.execute(get_over_due_todo.format( int(datestdtojd(today_date)))).fetchall()
                if res:
                    todo_array = []
                    for i in range(0, len(res)):
                        todo_array.append({'id':res[i][0], 
                        'task' :res[i][1],
                        'due_date': jdtodatestd(str(res[0][2])) , 
                        'status':res[i][3] } )
                    return todo_array
                else:
                    return "", 404
        except :
            return {""}


@ns.route('/due')
@ns.response(404, 'No todos found')
class duebydate(Resource):

    @login_required
    def get(self):
        due_task_date = request.args.get("due_date")
        fmt= r'%d-%m-%Y'
        form_date = datetime.datetime.strptime(str(due_task_date), "%Y-%m-%d").strftime(fmt)
        print(form_date)
        due_task_date = datestdtojd(form_date)
        try:
            with sqlite3.connect('todo_db.db') as conn:
                crsr = conn.cursor()
                res = crsr.execute(get_todo_date.format(due_task_date)).fetchall()
                if res:
                    todo_array = []
                    for i in range(0, len(res)):
                        todo_array.append({'id':res[i][0], 
                        'task' :res[i][1],
                        'due_date': jdtodatestd(str(res[0][2])) , 
                        'status':res[i][3] } )
                    return todo_array
                else:
                    return "", 404
        except:
            return ""


@ns.route("/adduser")
class UserAdmin(Resource):

    @login_required
    @admin_required
    @ns.response(200,"Data Successfully added")
    @ns.response(500,"Database Error")
    @ns.expect(user)
    def post(self):
        data = api.payload
        try:
            with sqlite3.connect('todo_db.db') as conn:
                crsr = conn.cursor()
                crsr.execute(insert_db_user,(data['username'],data['password'], data['isadmin']))
                conn.commit()
                return {'Success':'User added'}, 200
        except:
            return {'DataBase Failure': "Connection Error"}, 500

@ns.route('/deluser/<int:id>')
@ns.response(404, 'User not found')
@ns.param('id', 'The User identifier')
class UserDel(Resource):

    @login_required
    @admin_required
    @ns.response(200,"Data Successfully deleted")
    def delete(self,id):
        try:
            with sqlite3.connect('todo_db.db') as conn:
                crsr = conn.cursor()
                crsr.execute(delete_user.format(id))
                conn.commit()
                return {"Success":"Data deleted sucessfully"},200
        except:
            return {"Failure":"User not found"},404


@ns.route('/login/<username>/<password>')
@ns.response(404, 'User not found')
@ns.param('password', 'Enter your password')
@ns.param('username', 'Enter your username')
class UserLogin(Resource):

    @ns.response(200,"Login Successful")
    @ns.response(500,"Database Error")
    def get(self, username, password):
        try:
            with sqlite3.connect('todo_db.db') as conn:
                crsr = conn.cursor()
                res = crsr.execute(find_username.format(username)).fetchone()
                if res:
                    if res[2] == password:
                        session['username'] = res[1]
                        session['isadmin'] = res[3]
                        print(session)
                        return {"Success":"Login Successful"}, 200 
                    else:
                        return {"Login Failure":"Wrong passwod"}, 404
                else:
                    return {"Login Failure":"Username not found"},404
        except :
            return {'DataBase Failure': "Connection Error"}, 500


@ns.route('/logout')
@ns.response(200, 'Successfully logged out')
class UserLogout(Resource):
    @login_required
    def get(self):
        session.pop('username', None)
        session.pop('isadmin',None)
        return {"Success":"Loggedout"}


if __name__ == '__main__':
    app.run(debug=True)