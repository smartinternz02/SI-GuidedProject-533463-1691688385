from flask import Flask, render_template, request, session
import ibm_db
import ibm_boto3
from ibm_botocore.client import Config, ClientError
import os
import re
import random
import string
import datetime
import requests
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=fbd88901-ebdb-4a4f-a32e-9822b9fb237b.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=32731;UID=yms88774;PASSWORD=u9eRWpksHM33mXZd;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt","","")
print(conn)
print("Connection Successfull")

COS_ENDPOINT = "https://prashantstudent.s3.jp-tok.cloud-object-storage.appdomain.cloud"
COS_API_KEY_ID = "MyX-mvA9jC3Nd6IZdsLRIg8EMLZXW4T6pjMx50nKfxCt"
COS_INSTANCE_CRN = "crn:v1:bluemix:public:cloud-object-storage:global:a/ce2c0eb98c754e8287f7b5f407af741b:8502b471-4589-4c6c-af13-3ef1bb7f87c4::"
BUCKET_NAME = "prashantstudent"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/studentprofile")
def sprofile():
    if 'Loggedin' in session and session['Loggedin']:
        msg = "Welcome to your Student Profile!"
        user_email = session['email']
        user_name = session['name']
        user_username = session['username']
        user_role = session['role']
        return render_template("studentprofile.html", msg=msg, email=user_email, name=user_name, username=user_username, role=user_role)
    else:
        return render_template("login.html")


@app.route("/adminprofile")
def aprofile():
    return render_template("adminprofile.html")

@app.route("/facultyprofile")
def fprofile():
    return render_template("facultyprofile.html")

@app.route("/login", methods=['POST', 'GET'])
def login():
    global Userid
    global Username
    msg = ''
    if request.method == "POST":
        email = str(request.form['email'])
        print(email)
        password = request.form["password"]
        sql = "SELECT * FROM REGISTER WHERE EMAIL=? AND PASSWORD=?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, email)
        ibm_db.bind_param(stmt, 2, password)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        print(account)
        if account:
            session['Loggedin'] = True
            session['id'] = account['EMAIL']
            Userid = account['EMAIL']
            session['email'] = account['EMAIL']
            Username = account['USERNAME']
            Name = account['NAME']
            msg = "Logged in Successfully!"
            sql = "SELECT ROLE FROM register where email = ?"
            stmmt = ibm_db.prepare(conn, sql)
            ibm_db.bind_param(stmt, 1, email)
            ibm_db.execute(stmt)
            r = ibm_db.fetch_assoc(stmt)
            print(r)
            if r['ROLE'] == 1:
                print("STUDENT")
                return render_template("studentprofile.html", msg=msg, user=email, name=Name, role="STUDENT", username=Username, password=password, email=email)
            elif r['ROLE'] == 2:
                print("FACULTY")
                return render_template("facultyprofile.html", msg=msg, user=email, name=Name, role="FACULTY", username=Username, password=password, email=email)
            else:
                return render_template("adminprofile.html", msg=msg, user=email, name=Name, role="ADMIN", username=Username, password=password, email=email)
        else:
            msg = "Incorrect Email/Password!"
        
        return render_template("login.html", msg=msg)
    else:
        return render_template("login.html")


@app.route("/register", methods=["POST", "GET"])
def signup():
    msg=''
    if request.method == "POST":
        name = request.form["sname"]
        email = request.form["semail"]
        username = request.form["susername"]
        role = int(request.form['role'])
        password = ''.join(random.choice(string.ascii_letters) for i in range(0,8))
        link = 'https://university.ac.in/portal'
        print(password)
        sql = "SELECT * FROM register WHERE email = ?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, email)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        print(account)
        if account:
            msg = "Already Registered"
            return render_template('adminregister.html', error=True, msg=msg)
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = "Invalid Email Address!"
        else:
            insert_sql = "INSERT INTO register VALUES (?,?,?,?,?)"
            prep_stmt = ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(prep_stmt, 1, name)
            ibm_db.bind_param(prep_stmt, 2, email)
            ibm_db.bind_param(prep_stmt, 3, username)
            ibm_db.bind_param(prep_stmt, 5, role)
            ibm_db.bind_param(prep_stmt, 4, password)
            ibm_db.execute(prep_stmt)

            url = "https://rapidprod-sendgrid-v1.p.rapidapi.com/mail/send"

            payload = {
                "personalizations": [
                    {
                        "to": [{"email": email}],
                        "subject": "student Account Details"
                    }
                ],
                "from": {"email": "Prashant@university.com"},
                "content": [
                    {
                        "type": "text/plain",
                        "value": """Dear {}, \n 
                        Welcome to University, Here are the details to login into your student portal link : {} \n
                        YOUR USERNAME: {} \n
                        PASSWORD: {} \n
                        Thank You \n
                        Sincerely \n
                        Office of Admissions \n
                        University \n
                        Email: admission@university.ac.in ; Website: www.university.ac.in""".format( name, link, username, password)
                    }
                ]
            }
            headers = {
                "conntent-type": "application/json",
                "X-RapidAPI-Key": "afc75e0a03msh8e4df2083ca6fecp185340jsna85a2321e1c9",
                "X-RapidAPI-Host": "rapidprod-sendgrid-v1.p.rapidapi.com"
            }
            response = requests.request("POST", url, json=payload, headers=headers)
            print(response.text)
            msg = "Registration Successful"
    return render_template('adminregister.html', msg=msg)

@app.route("/studentsubmit", methods=['POST', 'GET'])
def sassignment():
    u = Username.strip()
    subtime = []
    ma = []
    sql = "SELECT SUBMITTIME, MARKS from SUBMIT WHERE STUDENTNAME = ?"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, u)
    ibm_db.execute(stmt)
    st = ibm_db.fetch_tuple(stmt)
    while st != False:
        subtime.append(st[0])
        ma.append(st[1])
        st = ibm_db.fetch_tuple(stmt)
    print(subtime)
    print(ma)
    
    submitted = [t if t else None for t in subtime]

    if request.method == "POST":
        for x in range(1, 6):  # Changed range to 1-6 for all 5 assignments
            y = "file" + str(x)
            if y in request.files:
                f = request.files[y]
                if f.filename != '':
                    basepath = os.path.dirname(__file__)
                    filepath = os.path.join(basepath, 'uploads', u + str(x) + ".pdf")
                    f.save(filepath)
                    print(filepath)
                    cos = ibm_boto3.client("s3", ibm_api_key_id=COS_API_KEY_ID, ibm_service_instance_id=COS_INSTANCE_CRN, config=Config(signature_version="oauth"), endpoint_url=COS_ENDPOINT)
                    print(cos)
                    cos.upload_file(Filename=filepath, Bucket=BUCKET_NAME, Key=u + str(x) + ".pdf")
                    
                    ts = datetime.datetime.now()
                    t = ts.strftime("%Y-%m-%d %H:%M:%S")
                    sql1 = "SELECT * FROM SUBMIT WHERE STUDENTNAME = ? AND ASSIGNMENTNUM = ?"
                    stmt = ibm_db.prepare(conn, sql1)
                    ibm_db.bind_param(stmt, 1, u)
                    ibm_db.bind_param(stmt, 2, x)
                    ibm_db.execute(stmt)
                    acc = ibm_db.fetch_assoc(stmt)
                    
                    if acc == False:
                        sql = "INSERT into SUBMIT (STUDENTNAME, ASSIGNMENTNUM, SUBMITTIME) values (?,?,?)"
                        stmt = ibm_db.prepare(conn, sql)
                        ibm_db.bind_param(stmt, 1, u)
                        ibm_db.bind_param(stmt, 2, x)
                        ibm_db.bind_param(stmt, 3, t)
                        ibm_db.execute(stmt)
                    else:
                        sql = "UPDATE SUBMIT SET SUBMITTIME = ? WHERE STUDENTNAME = ? and ASSIGNMENTNUM = ?"
                        stmt = ibm_db.prepare(conn, sql)
                        ibm_db.bind_param(stmt, 1, t)
                        ibm_db.bind_param(stmt, 2, u)
                        ibm_db.bind_param(stmt, 3, x)
                        ibm_db.execute(stmt)

        msg = "Uploading Successful"
        return render_template("studentsubmit.html", submitted=submitted, msg=msg, datetime=subtime, marks=ma)
    
    return render_template("studentsubmit.html", submitted=submitted, datetime=subtime, marks=ma)


@app.route("/studentlist")
def studentlist():
    data = []
    sql = "SELECT USERNAME from REGISTER WHERE Role=1"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.execute(stmt)
    name = ibm_db.fetch_tuple(stmt)
    while name != False:
        data.append(name)
        name = ibm_db.fetch_tuple(stmt)
    data1 = []
    for i in range(0, len(data)):
        y = data[i][0].strip()
        data1.append(y)
    data1 = set(data1)
    data1 = list(data1)
    print(data1)

    return render_template("facultystulist.html", names=data1, le=len(data1))

@app.route("/marksassign/<string:stdname>", methods=["POST", "GET"])
def marksassign(stdname):
    global u
    global g
    global file
    da = []
    cos = ibm_boto3.client("s3", ibm_api_key_id=COS_API_KEY_ID, ibm_service_instance_id=COS_INSTANCE_CRN, config=Config(signature_version="oauth"), endpoint_url=COS_ENDPOINT)
    output = cos.list_objects(Bucket="studentassignmentsb")
    output
    print(output)
    
    l = []
    for i in range(0,len(output['Contents'])):
        j = output['Contents'][i]['Key']
        l.append(j)
    l
    print(l)
    u = stdname
    print(len(u))
    print(len(l))
    n = []
    for i in range(0, len(l)):
        for j in range(0,len(u)):
            if u[j] == l[i][j]:
                n.append(l[i])
    
    file = set(n)
    file = list(file)
    print(file)
    print(len(file))
    g = len(file)
    sql = "SELECT SUBMITTIME from SUBMIT WHERE STUDENTNAME=?"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, u)
    ibm_db.execute(stmt)
    m = ibm_db.fetch_tuple(stmt)
    while m != False:
        da.append(m[0])
        m = ibm_db.fetch_tuple(stmt)

    print(da)
    return render_template("facultymarks.html", file=file, g=g, marks=0, datetime=da)

@app.route("/marksupdate/<string:anum>", methods=['POST', 'GET'])
def marksupdate(anum):
    ma = []
    da = []
    mark = request.form['mark']
    print(mark)
    print(u)
    sql = "UPDATE SUBMIT SET MARKS = ? WHERE STUDENTNAME = ? and ASSIGNMENTNUM = ?"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, mark)
    ibm_db.bind_param(stmt, 2, u)
    ibm_db.bind_param(stmt, 3, anum)
    ibm_db.execute(stmt)
    msg = "MARKS UPDATED"
    sql = "SELECT MARKS, SUBMITTIME from SUBMIT WHERE STUDENTNAME = ?"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, u)
    ibm_db.execute(stmt)
    m = ibm_db.fetch_tuple(stmt)
    while m != False:
        ma.append(m[0])
        da.append(m[1])
        m = ibm_db.fetch_tuple(stmt)

    print(ma)
    print(da)
    return render_template("facultymarks.html", msg=msg, marks=ma, g=g, file=file, datetime=da)

@app.route("/logout")
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return render_template("login.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")