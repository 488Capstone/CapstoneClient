from argparse import Namespace

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient

import logging
import json
import argparse

# TODO: AWSIOT - create policies, rules, topics



# Function called when a shadow is updated
def customShadowCallback_Update(payload, responseStatus, token):
    # Display status and data from update request
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")

    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Update request with token: " + token + " accepted!")
        print("moisture: " + str(payloadDict["state"]["reported"]["moisture"]))
        print("temperature: " + str(payloadDict["state"]["reported"]["temp"]))
        print("pressure (hPa): " + str(payloadDict["state"]["reported"]["pressure"]))
        print("zone current (mA): " + str(payloadDict["state"]["reported"]["zone_current"]))
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")

    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")


# Function called when a shadow is deleted
def customShadowCallback_Delete(payload, responseStatus, token):
    # Display status and data from delete request
    if responseStatus == "timeout":
        print("Delete request " + token + " time out!")

    if responseStatus == "accepted":
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Delete request with token: " + token + " accepted!")
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")

    if responseStatus == "rejected":
        print("Delete request " + token + " rejected!")


# AWSIoTMQTTShadowClient writes data to the log
def configureLogging():
    logger = logging.getLogger("AWSIoTPythonSDK.core")
    logger.setLevel(logging.DEBUG)
    streamHandler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)


def publish(payload):
    # possibility for payload format:
    #payload = { "state": { "moisture": str(moistureLevel), "temp": str(temp), "pressure (hPa)": str(pressure), "zone current (mA)": str(zone_current)}}

    args = parseArgs()  # Parse command line arguments. Since we won't be using this with CLI args, it sets default values.

    # init / configuration of MQTT Shadow Client
    myAWSIoTMQTTShadowClient = None
    myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(args.clientId)
    myAWSIoTMQTTShadowClient.configureEndpoint(args.host, args.port)
    myAWSIoTMQTTShadowClient.configureCredentials(args.rootCAPath, args.privateKeyPath, args.certificatePath)
    ####################################################################################################################

    # AWSIoTMQTTShadowClient connection configuration
    myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
    myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
    myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec
    ####################################################################################################################

    # Connect to AWSIoT
    try:
        myAWSIoTMQTTShadowClient.connect()
        print("Connected to AWSIoT.")
    except:
        print("Could not connect to AWSIoT shadow client.")

    # Create a device shadow handler, use this to update and delete shadow document
    try:
        deviceShadowHandler = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(args.thingName, True)
        print("shadow handler created.")
    except:
        print("could not create shadow handler.")

    # Delete current shadow JSON doc
    try:
        deviceShadowHandler.shadowDelete(customShadowCallback_Delete, 5)
        print("current shadow JSON doc deleted.")
    except:
        print("could not delete current shadow JSON doc.")

    # Update shadow
    try:
        deviceShadowHandler.shadowUpdate(json.dumps(payload), customShadowCallback_Update, 5)
    except:
        print("Could not update shadow.")


# Read in command-line parameters. sets defaults if no CLI args are passed.
def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e",  "--endpoint",  action="store", dest="host",            help="Your AWS IoT custom endpoint")
    parser.add_argument("-r",  "--rootCA",    action="store", dest="rootCAPath",      help="Root CA file path")
    parser.add_argument("-c",  "--cert",      action="store", dest="certificatePath", help="Certificate file path")
    parser.add_argument("-k",  "--key",       action="store", dest="privateKeyPath",  help="Private key file path")
    parser.add_argument("-p",  "--port",      action="store", dest="port",            help="Port number override",         type=int)
    parser.add_argument("-n",  "--thingName", action="store", dest="thingName",       help="Targeted thing name",          default="Bot")
    parser.add_argument("-id", "--clientId",  action="store", dest="clientId",        help="Targeted client id",           default="basicShadowUpdater")
    args = parser.parse_args()

# TODO: Collin set these default arguments so they'll only work for this device with these certs.
    # They will certainly need to be changed to allow other devices to function properly.

    # this endpoint will change to Nolan's AWSIoT endpoint.
    if not args.host:
        args.host = "a16860lqrlz0ti-ats.iot.us-east-1.amazonaws.com"

    # cert paths (next three entries) should be fine as long as the directory structure and naming convention are consistent.
    if not args.rootCAPath:
        args.rootCAPath = "/Users/collinturner/PycharmProjects/CapstoneClient/certs/AmazonRootCA1.pem"
    if not args.certificatePath:
        args.certificatePath = "/Users/collinturner/PycharmProjects/CapstoneClient/certs/certificate.pem.crt"
    if not args.privateKeyPath:
        args.privateKeyPath = "/Users/collinturner/PycharmProjects/CapstoneClient/certs/private.pem.key"

    # TODO: database
    if not args.thingName:
        args.thingName = "CapstoneClient"
    if not args.clientId:
        args.clientId = "CapstoneClient"
    if not args.port:
        args.port = 8883

    return args







