from flask import Flask, render_template, request, flash, redirect
from flask_restful import Api, Resource, reqparse
from flask_wtf import Form
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired
from emtoolkit.session import Controller
import requests
import json
import os

app = Flask(__name__)
app.secret_key = "qsdlkfjasdlkfjawlk4j324lj2wlkrfjasdlkfjsa"
api = Api(app)

APIC_EM = os.getenv("APIC_EM_URL", 'https://sandboxapic.cisco.com')
USERNAME = os.getenv("APIC_EM_USERNAME", 'devnetuser')
PASSWD = os.getenv("APIC_EM_PASSWORD", 'Cisco123!')
SPARK_TOKEN = os.getenv("SPARK_TOKEN")
SPARK_ROOM = os.getenv("SPARK_ROOM")
SESSION = Controller(APIC_EM, USERNAME, PASSWD)

def logo():
    """
    Check env for presence of custom logo
    :return:
    """
    return os.getenv("LOGO", "/static/img/logo.png")

def title():
    return os.getenv("TITLE", "App Registration")


class IPPortAppObject(object):

    def __init__(self, name, protocol="tcp", ip="", port="", kls="BULK_DATA"):
        self.attributes = [
            {"trafficClass": kls,
             "helpString": name,
             "name": name,
             "appProtocol": protocol,
             "transportIps": ip,
             "pfrThresholdJitter": 1,
             "pfrThresholdLossRate": 50,
             "pfrThresholdOneWayDelay": 500,
             "pfrThresholdJitterPriority": 1,
             "pfrThresholdLossRatePriority": 2,
             "pfrThresholdOneWayDelayPriority": 3,
             "category": "other",
             "subCategory": "other",
             "categoryId": "f1283ed8-14c2-420e-8d3f-8e9a48931a79",
             "engineId": 6,
             "rank": 1
             }
        ]
        if self.attributes[0]['appProtocol'] == 'tcp':
            self.attributes[0]["tcpPorts"] = port
        elif self.attributes[0]['appProtocol'] == 'udp':
            self.attributes[0]["udpPorts"] = port

    def json(self):
        return self.attributes

    @property
    def name(self):
        return self.attributes[0]['name']

    @property
    def protcol(self):
        return self.attributes[0]['protocol']

    @property
    def port(self):
        return self.attributes[0]['protocol']


class UrlAppObject(object):

    def __init__(self, name, url, kls="BULK_DATA"):
        self.attributes = [
            {"trafficClass": kls,
             "helpString": name,
             "name": name,
             "appProtocol": "tcp",
             "url": url,
             "pfrThresholdJitter": 1,
             "pfrThresholdLossRate": 50,
             "pfrThresholdOneWayDelay": 500,
             "pfrThresholdJitterPriority": 1,
             "pfrThresholdLossRatePriority": 2,
             "pfrThresholdOneWayDelayPriority": 3,
             "category": "other",
             "subCategory": "other",
             "categoryId": "f1283ed8-14c2-420e-8d3f-8e9a48931a79",
             "engineId": 6,
             "rank": 1
             }
        ]

    def json(self):
        return self.attributes

    @property
    def name(self):
        return self.attributes[0]['name']

    @property
    def url(self):
        return self.attributes[0]['url']


class IPPortAppForm(Form):

    name = StringField('name', validators=[DataRequired()])
    protocol = SelectField('protocol',
                           choices=[('tcp', 'tcp'),
                                    ('udp', 'udp')])
    ip = StringField('ip')
    port = StringField('port')
    kls = SelectField('kls', choices=[
        ('TRANSACTIONAL_DATA', 'TRANSACTIONAL_DATA'),
        ('BULK_DATA', 'BULK_DATA')
    ]
                      )


class UrlAppForm(Form):

    name = StringField('name', validators=[DataRequired()])
    url = StringField('url', validators=[DataRequired()])
    kls = SelectField('class', choices=[
        ('TRANSACTIONAL_DATA', 'TRANSACTIONAL_DATA'),
        ('BULK_DATA', 'BULK_DATA')
    ])


def send_spark_notifciation(app_name):
    msgdata = {
        "roomId": SPARK_ROOM,
        "text": "A new application named {} "
                "was provisioned via the app registry".format(app_name)
    }
    headers = {"Authorization": "Bearer {}".format(SPARK_TOKEN),
               "Content-type": "application/json; charset=utf-8"}

    resp = requests.post('https://api.ciscospark.com/v1/messages',
                         headers=headers,
                         data=json.dumps(msgdata))
    print resp.text


@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        return render_template('appform.html',
                               title=title(),
                               logo=logo())


@app.route('/app/url', methods=['GET', 'POST'])
def appurl():
    if request.method == 'GET':
        form = UrlAppForm()
        return render_template('urlapp.html',
                               title=title(),
                               logo=logo(),
                               form=form)

    if request.method == 'POST':
        print request
        print request.form
        print request.data

        form = UrlAppForm(request.form)
        if form.validate():
            print 'creating new app object'
            newapp = UrlAppObject(form.name.data,
                                  form.url.data,
                                  kls=form.kls.data)
            print newapp.name
            print newapp.url

            respjson = SESSION.post('/application', newapp.json())
            print respjson

            if 'url' in respjson['response']:
                flash('Thanks for registering your app',
                      category="alert-success")
                send_spark_notifciation("{}".format(form.name.data))

            else:
                flash('There was a problem registering your app',
                      category="alert-danger")

            return redirect('/')


@app.route('/app/ipport', methods=['GET', 'POST'])
def ipport():
    if request.method == 'GET':
        form = IPPortAppForm()
        return render_template('ipportapp.html',
                               title=title(),
                               logo=logo(),
                               form=form)

    if request.method == 'POST':
        print request
        print request.form
        form = IPPortAppForm(request.form)

        if form.validate():
            print 'creating new app object'
            newapp = IPPortAppObject(name=form.name.data,
                                     ip=form.ip.data,
                                     port=form.port.data,
                                     protocol=form.protocol.data,
                                     kls=form.kls.data)

            respjson = SESSION.post('/application', newapp.json())

            if respjson:
                flash('Thanks for registering your app',
                      category="alert-success")
                send_spark_notifciation("{}".format(form.name.data))

            else:

                flash('There was a problem registering your app',
                      category="alert-danger")

            return redirect('/')

parser = reqparse.RequestParser()
parser.add_argument('LOGO')
parser.add_argument("TITLE")

class Customize(Resource):
    def post(self):
        args = parser.parse_args()
        print args
        if "LOGO" in args.keys():
            os.environ["LOGO"] = args["LOGO"]
        if "TITLE" in args.keys():
            os.environ["TITLE"] = args["TITLE"]
        return {"TITLE": title(),
                "LOGO": logo()
                }

api.add_resource(Customize, '/api/customize')


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=os.getenv("DEBUG", False))
