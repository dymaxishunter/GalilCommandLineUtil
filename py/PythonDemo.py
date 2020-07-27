from __future__ import print_function, unicode_literals
from PyInquirer import prompt, print_json, style_from_dict, separator, Token
from examples import custom_style_2
from pprint import pprint
import sys
import time
import string
import gclib
import PyInquirer

DETECTATTEMPTS = 1


def main():
    print('\nWelcome to the Dymaxis Galil IKO Demo Program\n')
    print('This program is configured to run a DMC-4040 with the IKO Linear motor connected to Axis D\n')

    g = gclib.py() #make an instance of the gclib python class
    G_IP_Addr = '192.168.1.54'

    connected = ListAndConnectToController(g)
    exitLoop = False
    if (connected == 1):
        configureIKOLinear(g)
        while(not(exitLoop)):
            questions = [                
                {
                    'type': 'list',
                    'name': 'command',
                    'message': 'What would you like to run?',
                    'choices': ['Enable Motor','Disable Motor', 'Homing', 'Set Speed', 'Manual Command','IKO Linear Motor Loop', 'Disconnect and Exit'],                    
                },                 
            ]

            answers = prompt(questions, style=custom_style_2)
            cmd = answers.get('command')

            if (cmd=='Enable Motor'):
                g.GCommand('SHD')
            elif(cmd=='Disable Motor'):
                g.GCommand('MOD')
            elif(cmd=='Homing'):
                #Need to implement
                print('\nCurrent homing method is set current position = 0.\n')
                g.GCommand('DPD=0')
            elif(cmd=='Set Speed'):
                curSpeed = g.GCommand('SPD=?')
                print('Current speed is: %s [counts/s]' %curSpeed)
                speed = input('Set new speed to ... [counts/s] ')
                g.GCommand('SPD=%s'%speed)
            elif(cmd=='Manual Command'):
                tmpCmd = input('Enter command to send:\n')               
                try:
                    g.GCommand(tmpCmd)
                except gclib.GclibError as e:
                    print('Exception caught sending command %s'%e)
            elif( cmd =='IKO Linear Motor Loop'):
                runMoveLoop(g)
            elif( cmd =='Disconnect and Exit'):
                exitLoop = True


        disconnectController(g)
        print('\nThank you for running the Dymaxis Python Demo. Exiting Program')
    else:
        print("\nConnection failed. Make sure PC is on the same subnet as the controller. \n\nExiting Program")       

    return

#####################################################
#  
# List all galil controllers and allow user to select one from a list. 
# Function will connect to controller and return 1 if successful and -1 if unsucessful
# 
#####################################################
def ListAndConnectToController(GC: gclib.py()):
    #Get Ethernet controllers requesting IP addresses
    
    # USE GC.GIpRequests() for controllers without assigned IP address 
    # Every new line is a new controller (use split statment)
    # Each line contains the following info: 
    #       [Model #], [Serial #], [MAC Address], [Connection Name], [IP Address]
    print('\nListening for controllers requesting IP addresses... 0')
    ip_requests = GC.GIpRequests()
    controllerListNoIp = []
    i=1
    
    while ((ip_requests.__len__() == 0) and (i < DETECTATTEMPTS)):
        print('Listening for controllers requesting IP addresses... ', i)
        ip_requests = GC.GIpRequests()
        i+=1
    # end while

    if (i > DETECTATTEMPTS):
        print("    No Controllers detected requesting an IP address")
        NoIpDetected = False
    else:
        print("   Controllers detected requesting an IP address")
        NoIpDetected = True       
        for id in sorted(ip_requests.keys()):
            controllerListNoIp.append(id)


    # Use GC.GAddresses() for controllers already assigned IP address 
    print('\nListening for controllers with assigned addresses...0') #print ready connections
    detectedControllers = GC.GAddresses()
    controllerList = [];
    i=1
    while ((detectedControllers.__len__() == 0) and (i < DETECTATTEMPTS)):
        detectedControllers = GC.GAddresses()
        i+=1
        print("Listening for controllers with assigned addresses... ", i)
    # end while

    if (i > DETECTATTEMPTS):
        print("    No Controllers detected with an assigned IP address")
        withIpDetected = False
    else:        
        print("    Controllers detected with an assigned IP address")
        for a in sorted(detectedControllers.keys()):
            controllerList.append(a)
            # print(a, detectedControllers[a])

        withIpDetected = True

    if (withIpDetected):
        questions = [            
            {
                'type': 'list',
                'name': 'controller',
                'message': 'What controller do you want to connect to?',
                'choices': controllerList,
                'filter': lambda val: val.lower()
            },
                ############ implement IP address update at a later time ############
            # {
            #     'type': 'list',
            #     'name': 'ipUpdate',
            #     'message': 'would you like to update the IP address?',
            #     'choices': ['yes','no'],
            # },
        ]

        answers = prompt(questions, style=custom_style_2)
        # pprint(answers)

        controllerIP = answers.get('controller')

        ############ implement IP address update at a later time ############
        # if answers.get('ipUpdate').__eq__('yes'):
        #     newIP = input("\nEnter the new IP address: ")
        #     if (newIP.count('.') != 3):
        #         print("Invalid IP address. Ending program because I'm lazy")
        #         return
        #     controllerIP = updateIP(GC,newIP, controllerIP)

        
        try:
            connectController(GC, controllerIP)
            return 1
        except gclib.GclibError as e:
            print('Unexpected GclibError:', e)
            return -1
    else: 
        return -1

    return

def connectController(GC: gclib.py(), IPAddr: string, printInfo: bool=True):
    GC.GOpen(IPAddr + ' --direct -s ALL')
    if printInfo:
        print(GC.GInfo())
    return

def disconnectController(GC: gclib.py()):
    GC.GClose()     
    return


def assignIP(GC: gclib.py(), newIPAddr: string, currentIPAddr: string):       
    GC.GAssign(newIPAddr, currentIPAddr) #send the mapping
    GC.GOpen(newIPAddr + ' --direct')
    GC.GCommand('BN') #burn the IP
    disconnectController(GC) #disconnect
    return newIPAddr

def updateIP(GC: gclib.py(), newIPAddr: string, currentIPAddr: string):       
    GC.GOpen(currentIPAddr + ' --direct')
    sendstring = 'IA  %s' %newIPAddr
    sendstring=sendstring.replace('.',',')
    try:
        GC.GCommand(sendstring)
    except gclib.GclibError as e:
        GC.GClose()
        print('exception caught, waiting for IP to update and attempting reconnect')
        time.sleep(5000)
        GC.GOpen(newIPAddr + ' --direct')

    GC.GCommand('BN') #burn the IP
    disconnectController(GC) #disconnect

    return newIPAddr

def configureIKOLinear(GC: gclib.py()):
    GC.GCommand('STD')
    GC.GMotionComplete('D')
    GC.GCommand('MOD')
    GC.GCommand('BAD')
    GC.GCommand('AGD=0')
    GC.GCommand('AUD=8')
    GC.GCommand('BZD=2')

    GC.GCommand('TM=1000.0')
    GC.GCommand('KDD=60.0')
    GC.GCommand('KPD=5.0')
    GC.GCommand('KID=0.05')
    GC.GCommand('TLD=5.0')
    
    # GC.GCommand('ERD=20000.0')    # Set position error limit
    GC.GCommand('OED=0')            # Disable "MO on Position Error Exceeded" 
    GC.GCommand('SPD=100000.0')
    GC.GCommand('ACD=150000.0')
    GC.GCommand('DCD=150000.0')

    



def runMoveLoop(GC: gclib.py()):
    loopCount = int(input("How many loops would you like to run?  "))
    distance = float(input("What distance would you like to index [mm]?\n(Max stroke is 18mm)\n" ))
    if ((distance > 18 ) or (distance < 0)):
        print('Invalid Distance. Exiting IKO Linear Motor Loop')
        return
    
    encoderDist = distance / 0.0001 # 0.1um accuracy encoder

    i = 0
    try:
        print('\nStarting Move Loop. Press Ctrl+C to exit loop after next move completes.\n')
        while (i < loopCount):
            GC.GCommand('PAD=%i'%encoderDist)
            GC.GCommand('BG D')
            GC.GMotionComplete('D')
            GC.GCommand('PAD=0')
            GC.GCommand('BG D')
            GC.GMotionComplete('D')
            print('Loop %i'%i)
            i+=1
    except KeyboardInterrupt:   
        print('Exiting loop - Keyboard interrupt\n')
        return
    
    print()
    return
  
#runs main() if example.py called from the console
if __name__ == '__main__':
  main()