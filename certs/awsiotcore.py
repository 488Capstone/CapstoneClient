from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

myMQTTClient = AWSIoTMQTTClient("CollinClientID") # random key, if another connection
myMQTTClient.configureEndpoint("a20pl4sdwe06wd-ats.iot.us-east-1.amazonaws.com", 8883)

myMQTTClient.configureCredentials("AmazonRootCA1.pem",
                                  "4acf5c3eb9-private.pem.key",
                                  "4acf5c3eb9-certificate.pem.crt")

myMQTTClient.configureOfflinePublishQueueing(-1) #infinite offline publishing
myMQTTClient.configureDrainingFrequency(2) # draining: 2Hz
myMQTTClient.configureConnectDisconnectTimeout(10) #10sec
myMQTTClient.configureMQTTOperationTimeout(5) # 5sec
print('Initializing IoT Core Topic ...')
myMQTTClient.connect()

myMQTTClient.publish(
    topic="device/2/data", # change to 'device/2/data'for thing2
    QoS=1,
    payload="""
    {
        "temperature": 43,
        "moisture": 51,
        "status": 0
    }
    """)