import json
from flask import Flask, Response, request

from cpa import cpa

VALID_PARAMS = cpa.parameters.keys()

app = Flask(__name__)

@app.route("/")
def online():
    res = dict()
    res['success'] = True
    res['message'] = "CPA controller server is online."
    res['version'] = cpa.parameters["VER"]
    res = json.dumps(res)
    return Response(res, status=200, mimetype='application/json')

@app.route("/connect")
def connect():
    cpa.open()
    res = dict()
    res['success'] = True
    res['message'] = "CPA is now in remote control mode."
    res['version'] = cpa.parameters["VER"]
    res['232'] = cpa.parameters["232"]
    res = json.dumps(res)
    return Response(res, status=200, mimetype='application/json')

@app.route("/disconnect")
def disconnect():
    cpa.close()
    res = dict()
    res['success'] = True
    res['message'] = "CPA is now in local control mode."
    res['version'] = cpa.parameters["VER"]
    res['232'] = cpa.parameters["232"]
    res = json.dumps(res)
    return Response(res, status=200, mimetype='application/json')

@app.route("/settings/<param_name>/", methods=['GET', 'PUT'])
@app.route("/settings/<param_name>/<channel>/", methods=['GET', 'PUT'])
def handle_parameter(param_name, channel=''):
    if param_name not in VALID_PARAMS:
        res = dict()
        res['success'] = False
        res['message'] = f"Invalid parameter name: {param_name}"
        res['version'] = cpa.parameters["VER"]
        res = json.dumps(res)
        return Response(res, status=404, mimetype='application/json')

    res = dict()
    if request.method == 'GET':
        cpa.get_parameter(param_name, channel)
        res['success'] = True
        res['message'] = f"Parameter '{param_name}' for channel '{channel}' retrieved successfully." if channel else f"Parameter '{param_name}' retrieved successfully."
        res['version'] = cpa.parameters["VER"]
        res[param_name] = cpa.parameters[param_name]
    elif request.method == 'PUT':
        value = request.get_json().get('value')
        if value is None:
            res['success'] = False
            res['message'] = "Value must be provided as a query parameter for PUT requests."
            res['version'] = cpa.parameters["VER"]
            res = json.dumps(res)
            return Response(res, status=400, mimetype='application/json')
        cpa.set_parameter(param_name, channel=channel, value=value)
        res['success'] = True
        res['message'] = f"Parameter '{param_name}' for channel '{channel}' updated successfully." if channel else f"Parameter '{param_name}' updated successfully."
        res['version'] = cpa.parameters["VER"]
        res[param_name] = cpa.parameters[param_name]
    res = json.dumps(res)
    return Response(res, status=200, mimetype='application/json')

@app.route("/set_current/<laser>/<value>")
def set_current_safely(laser, value):
    laser = int(laser)
    value = int(value)
    cpa.set_current_safely(laser=laser, current=value)
    res = dict()
    res['success'] = True
    res['message'] = f"Laser {laser} current set to {value} safely."
    res['version'] = cpa.parameters["VER"]
    if laser == 1:
        res['CUS'] = cpa.parameters["CUS"]
    elif laser == 2:
        res['C2S'] = cpa.parameters["C2S"]
    res = json.dumps(res)
    return Response(res, status=200, mimetype='application/json')

@app.route("/laser_on/")
def laser_on_safely():
    cpa.laser_on_safely()
    res = dict()
    res['success'] = True
    res['message'] = "Lasers turned on safely."
    res['version'] = cpa.parameters["VER"]
    res['LSR'] = cpa.parameters["LSR"]
    res['SHU'] = cpa.parameters["SHU"]
    res = json.dumps(res)
    return Response(res, status=200, mimetype='application/json')

@app.route("/save/")
def save_parameters():
    cpa.save_parameters()
    res = dict()
    res['success'] = True
    res['message'] = "Parameters saved to disk successfully."
    res['version'] = cpa.parameters["VER"]
    res = json.dumps(res)
    return Response(res, status=200, mimetype='application/json')