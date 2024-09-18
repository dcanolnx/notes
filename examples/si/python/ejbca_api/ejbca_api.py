#!/bin/python3

import datetime
import flask
from flask import jsonify
from flask import request
from flask import send_from_directory
import subprocess
import mysql.connector
import os

db_user = "ejbca"
db_password = ""
db_name = "ejbca"
tmp_directory = "/mnt/ejbca-api"

if not os.path.exists(tmp_directory):
    os.makedirs(tmp_directory)

def mysql_query(query):
    mydb = mysql.connector.connect(
        host="localhost",
        user=db_user,
        password=db_password,
        database=db_name
    )
    mycursor = mydb.cursor()
    mycursor.execute(query)
    results = mycursor.fetchall()
    return results


# Returns mail from table UserData using username from table CertificateData
def get_mail_username(username):
    sql = "select subjectEmail from UserData where username='" + str(username) + "';"
    try:
        return mysql_query(sql)[0][0].decode("utf-8")
    except:
        return ""


# Return user certificate Status
def user_cert_status(output_command):
    if "Status: 10" in output_command:
        return "New"
    if "Status: 40" in output_command:
        return "Generated"
    if "Status: 0" in output_command:
        return "Invalid"
    return "Unknown"


app = flask.Flask(__name__)
# app.config["DEBUG"] = True
app.config["ENV"] = "production"
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
app.config["SERVER_NAME"] = "erbio.int.stratio.com:5000"


@app.route('/', methods=['GET'])
def paths():
    return jsonify([{"path": "/", "method": "GET", "description": "Show this help"},
                    {"path": "/users", "method": "GET", "description": "Get all users: "
                                                                       "{user, expirationDate, mail}"},
                    {"path": "/users", "method": "POST", "description": "Create a new user. Need json", "json Format":
                        {"username":  "Username",
                         "givenName": "User first name",
                         "surname":   "User Last Name(s)",
                         "team":      "User team",
                         "country":   "User country, format ISO 3166 (ES,CO...)"}
                     },
                    {"path": "/users/certificate", "method": "GET", "description": "Download user cert. Need params in url: username, password"},
                    {"path": "/users/<username>", "method": "GET", "description": "Get <username> info: {user, "
                                                                                  "expirationDate, mail}"},
                    {"path": "/users/<username>", "method": "POST", "description": "Renew the username certificate"},
                    {"path": "/users/<username>", "method": "DELETE", "description": "Delete the username"},
                    {"path": "/users/days/<days>", "method": "GET", "description": "Get all users certificate expire "
                                                                                   "next x days"},
                    {"path": "/users/days/", "method": "GET", "description": "Get all users with certificate expired"},
                    {"path": "/rundeck/users", "method": "GET", "description": "Get all users (rundeck format)"}])


@app.route('/users', methods=['GET'])
def users_certs():
    certificates = []
    sql = "select username, MAX(expireDate) expireDate from CertificateData group by username;"
    search = mysql_query(sql)
    for result in search:
        user = result[0].decode("utf-8")
        expiration = result[1]
        ts_epoch = int(str(expiration)) / 1000
        ts = datetime.datetime.fromtimestamp(ts_epoch)  # .strftime('%Y-%m-%d %H:%M:%S')
        mail = get_mail_username(user)
        if mail != "" and mail.endswith("@stratio.com"):
            certificates.append({"user": user, "expiration": str(ts), "mail": mail})
    return jsonify(certificates), 200


@app.route('/users/<username>', methods=['GET'])
def user_cert(username):
    sql = "select username, MAX(expireDate) expireDate from CertificateData where username='" + username + "' group by username;"
    search = mysql_query(sql)
    for result in search:
        user = result[0].decode("utf-8")
        expiration = result[1]
        ts_epoch = int(str(expiration)) / 1000
        ts = datetime.datetime.fromtimestamp(ts_epoch)  # .strftime('%Y-%m-%d %H:%M:%S')
        mail = get_mail_username(user)
        if mail != "" and mail.endswith("@stratio.com"):
            command_search = "/opt/ejbca/bin/ejbca.sh ra findendentity --username " + username
            output = subprocess.getoutput(command_search)
            if "does not exist." in str(output):
                return jsonify({"message": "User not found"}), 404
            status = user_cert_status(str(output))
            return jsonify({"user": user, "expiration": str(ts), "mail": mail, "status": status}), 200
    return jsonify({"message": "User not found"}), 404


@app.route('/users/days/<days>', methods=['GET'])
def users_certs_days(days):
    certificates = []
    sql = "select username, MAX(expireDate) expireDate from CertificateData where status = '20' group by username;"
    search = mysql_query(sql)
    for result in search:
        user = result[0].decode("utf-8")
        expiration = result[1]
        ts_epoch = int(str(expiration)) / 1000
        ts = datetime.datetime.fromtimestamp(ts_epoch)  # .strftime('%Y-%m-%d %H:%M:%S')
        mail = get_mail_username(user)
        if mail != "" and mail.endswith("@stratio.com") and \
                datetime.datetime.today() + datetime.timedelta(days=float(days)) > \
                datetime.datetime.fromtimestamp(ts_epoch) > datetime.datetime.today():
            certificates.append({"user": user, "expiration": str(ts), "mail": mail})
    return jsonify(certificates), 200


@app.route('/users/days', methods=['GET'])
def users_certs_expired():
    certificates = []
    sql = "select username, MAX(expireDate) expireDate from CertificateData where status = '20' group by username;"
    search = mysql_query(sql)
    for result in search:
        user = result[0].decode("utf-8")
        expiration = result[1]
        ts_epoch = int(str(expiration)) / 1000
        ts = datetime.datetime.fromtimestamp(ts_epoch)  # .strftime('%Y-%m-%d %H:%M:%S')
        mail = get_mail_username(user)
        if datetime.datetime.today() > datetime.datetime.fromtimestamp(ts_epoch):
            certificates.append({"user": user, "expiration": str(ts), "mail": mail})
    return jsonify(certificates), 200


@app.route('/users/<username>', methods=['POST'])
def user_cert_update(username):
    command = "/opt/ejbca/bin/ejbca.sh ra setendentitystatus -S 10  --username " + username
    try:
        subprocess.check_output(command, shell=True)
        password = ""
        with open("/opt/wildfly/standalone/log/server.log", 'r') as read_obj:
            nextLine = False
            for line in read_obj:
                if nextLine:
                    password = line.split(": ")[1][0:9].strip()
                    nextLine = False
                if "Username: " + username in line:
                    nextLine = True
        return jsonify({"password": password}), 200
    except subprocess.CalledProcessError:
        return jsonify({"message": "User not found"}), 404


@app.route('/users/<username>', methods=['DELETE'])
def user_cert_del(username):
    command = "/opt/ejbca/bin/ejbca.sh ra revokeendentity -r 5 --username " + username
    try:
        subprocess.check_output(command, shell=True)
    except subprocess.CalledProcessError:
        return jsonify({"message": "User not found"}), 404
    command = "/opt/ejbca/bin/ejbca.sh ra delendentity --username " + username
    try:
        subprocess.run(command, shell=True, input=b"y")
        return jsonify({}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"message": str(e.output).split("b\'")[1].split("\'")[0]}), 400


@app.route('/users', methods=['POST'])
def user_cert_create():

    request_data = request.get_json()
    command = " cd /opt/ejbca/dist/clientToolBox/ && " \
              "/opt/ejbca/dist/clientToolBox/ejbcaClientToolBox.sh EjbcaWsRaCli edituser "
    username = request_data['username']
    givenName = request_data['givenName']
    surname = request_data['surname']
    team = request_data['team']
    country = request_data['country']

    command_search = "/opt/ejbca/bin/ejbca.sh ra findendentity --username " + username
    output = subprocess.getoutput(command_search)
    if "does not exist." not in str(output):
        return jsonify({"message": "User already exists"}), 400

    params = username + \
             " null false " \
             "\"[E=" + username + "@stratio.com](mailto:E=" + username + "@stratio.com),CN=" + username + \
             ",GIVENNAME=" + givenName + ",SURNAME=" + surname + ",OU=" + team + ",O=Stratio Big Data Inc,C=" + \
             country + ",EMAILADDRESS=" + username + "@stratio.com\" NULL \"" + username + "@stratio.com\" " \
             "\"Stratio Users\" 256 P12 NEW STRATIO\_ENDUSER STRATIO\_ENDUSER"
    try:
        subprocess.run(command+params, shell=True, input=b"y")
    except subprocess.CalledProcessError as e:
        return jsonify({"message": str(e.output).split("b\'")[1].split("\'")[0]}), 400

    password = ""
    with open("/opt/wildfly/standalone/log/server.log", 'r') as read_obj:
        nextLine = False
        for line in read_obj:
            if nextLine:
                password = line.split(": ")[1][0:9].strip()
                nextLine = False
            if "Username: " + username in line:
                nextLine = True
    return jsonify({"password": password}), 200


@app.route('/users/certificate', methods=['GET'])
def user_cert_download():
    command = "cd /opt/ejbca/dist/clientToolBox/ && " \
              "/opt/ejbca/dist/clientToolBox/ejbcaClientToolBox.sh EjbcaWsRaCli pkcs12req "
    username = request.args.get('username')
    password = request.args.get('password')

    command = command + username + " " + password + " 4096 RSA NONE " + tmp_directory
    try:
        subprocess.check_output(command, shell=True)
        return send_from_directory(tmp_directory, username+".p12", as_attachment=True)
    except subprocess.CalledProcessError as e:
        return jsonify({"message": str(e.output).split("b\'")[1].split("\'")[0]}), 500


@app.route('/rundeck/users', methods=['GET'])
def users_certs_rundeck():
    certificates = []
    sql = "select username, MAX(expireDate) expireDate from CertificateData group by username;"
    search = mysql_query(sql)
    for result in search:
        user = result[0].decode("utf-8")
        mail = get_mail_username(user)
        if mail != "" and mail.endswith("@stratio.com"):
            certificates.append(user)
    return jsonify(certificates), 200


app.run()

