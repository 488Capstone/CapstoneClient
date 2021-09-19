import json
import paho.mqtt.client as paho
import ssl


# todo: paths on device for aws mqtt keys
aws_host = "a20pl4sdwe06wd-ats.iot.us-east-1.amazonaws.com"
ca_path = "/home/pi/AWSiOT/root-ca.pem"
cert_path = "/home/pi/AWSiOT/certificate.pem.crt"
key_path = "/home/pi/AWSiOT/private.pem.key"
aws_port = 8883
client_id = "paho-thing1"

mqttc = paho.Client(client_id)
mqttc.tls_set(ca_path, certfile=cert_path, keyfile=key_path, cert_reqs=ssl.CERT_REQUIRED,
              tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print('connected')
    else:
        print('connect error')


def on_message(client, userdata, msg):
    payload = json.loads(msg.payload)
    print(f'RECEIVED MESSAGE: {payload}')


mqttc.on_connect = on_connect
mqttc.on_message = on_message


def get_device_shadow():
    # todo: topic from device file
    topic = "$aws/things/Thing1/shadow/get"
    payload = json.dumps("")

    mqttc.subscribe(topic + "/accepted", 1)


mqttc.connect(aws_host, aws_port, keepalive=60)
mqttc.loop_start()

get_device_shadow()

