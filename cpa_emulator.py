import json
from flask import Flask, Response, request

class CPAEmulator:
    def __init__(self):
        self.parameters = dict()
        with open('cpa_parameters.json', 'r') as f:
            self.parameters = json.load(f)

cpa = CPAEmulator()

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

@app.route("/favicon.ico")
def favicon():
    return Response(status=204)

@app.route("/connect/")
def connect():
    res = dict()
    res['success'] = True
    res['message'] = "CPA is now in remote control mode."
    res['version'] = cpa.parameters["VER"]
    res['232'] = cpa.parameters["232"]
    res = json.dumps(res)
    return Response(res, status=200, mimetype='application/json')

@app.route("/disconnect/")
def disconnect():
    res = dict()
    res['success'] = True
    res['message'] = "CPA is now in local control mode."
    res['version'] = cpa.parameters["VER"]
    res['232'] = cpa.parameters["232"]
    res = json.dumps(res)
    return Response(res, status=200, mimetype='application/json')

@app.route("/<param_name>/", methods=['GET', 'PUT'])
@app.route("/<param_name>/<channel>/", methods=['GET', 'PUT'])
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
        else:
            cpa.cpa.parameters[param_name] = value
            res['success'] = True
            res['message'] = f"Parameter '{param_name}' for channel '{channel}' updated successfully." if channel else f"Parameter '{param_name}' updated successfully."
            res['version'] = cpa.parameters["VER"]
            res[param_name] = cpa.parameters[param_name]
    res = json.dumps(res)
    return Response(res, status=200, mimetype='application/json')

@app.route("/set_current/<laser>/<value>/")
def set_current_safely(laser, value):
    laser = int(laser)
    value = int(value)
    cpa.parameters["CUS"] = value
    cpa.parameters["C2S"] = value
    res = dict()
    res['success'] = True
    res['message'] = f"Laser {laser} current set to {value} safely."
    res['version'] = cpa.parameters["VER"]
    if laser == 1:
        res['CRS'] = cpa.parameters["CRS"]
    elif laser == 2:
        res['C2S'] = cpa.parameters["C2S"]
    res = json.dumps(res)
    return Response(res, status=200, mimetype='application/json')

@app.route("/laser_on/")
def laser_on_safely():
    cpa.parameters["LSR"] = "ON"
    cpa.parameters["SHU"] = "ON"
    res = dict()
    res['success'] = True
    res['message'] = "Lasers turned on safely."
    res['version'] = cpa.parameters["VER"]
    res['LSR'] = cpa.parameters["LSR"]
    res['SHU'] = cpa.parameters["SHU"]
    res = json.dumps(res)
    return Response(res, status=200, mimetype='application/json')