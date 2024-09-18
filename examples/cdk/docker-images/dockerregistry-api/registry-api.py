#!/usr/bin/python3
import datetime
import flask
from flask import jsonify
from flask import request
from flask import send_from_directory
import subprocess
import os

def main():
    app = flask.Flask(__name__)
    # app.config["DEBUG"] = True
    app.config["ENV"] = "production"
    app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
    #app.config["SERVER_NAME"] = "docker-registry:9000"
    
    @app.route('/', methods=['GET'])
    def paths():
        return jsonify([{"path": "/", "method": "GET", "description": "Show this help"},{"path": "/garbage-collect", "method": "GET", "description": "Execute: $ registry garbage-collect"}])
    
    @app.route('/garbage-collect', methods=['GET'])
    def users_certs():
        certificates = []
        ip_address = flask.request.remote_addr
        if ip_address == "127.0.0.1":
            command="/bin/registry garbage-collect /etc/docker/registry/config.yml > /var/log/garbage-collect"
            print("Exec: "+command)
            subprocess.check_output(command, shell=True)
            return jsonify(certificates), 200
        else:  
            print(ip_address)
            return jsonify("This can be only executed from 127.0.0.1"), 401

    app.run(port=1234)

if __name__ == "__main__":
    main()
