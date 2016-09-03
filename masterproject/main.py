import re
import subprocess
from novaclient import client
from time import sleep 

nova = client.Client(2, 's177437', 'cried hang express', 'awtconsulting','http://128.39.120.14:5000/v2.0/' )

def runbash(command):
    bashcommand = subprocess.call(command, shell=True)

def getbash(command):
    bashcommand = subprocess.Popen(command,stdout=subprocess.PIPE, shell=True)
    (bashOutput, err) = bashcommand.communicate()
    return bashOutput


class webmanager:
    webservers = []
    maxwebservers = 0
    currentWebservers = 0
    minWebservers = 0
    maxConnections = 0
    
    def __init__(self, maxwebservers, minWebservers, maxConnections, minConnections):
        self.maxwebservers = maxwebservers
        self.minwebservers = minWebservers
        self.maxConnections = maxConnections
        self.minConnections = minConnections 
        self.createWebServer()

    def createWebServer(self):
        hostname = 'webserverJostein' + str(self.currentWebservers + 1)
        print self.maxwebservers
        if (self.currentWebservers + 1 < self.maxwebservers):
            newServer = webserver(hostname)
            self.webservers.append(newServer)
            print self.webservers
            self.currentWebservers += 1
            return True
        else:    
            print "throw exception\n"
            return False

    def deleteWebServer(self):
        self.currentWebservers -= 1
        del self.webservers[-1]

        
    def exception(self, hostname):
        print "ERROR: The webserver " + hostname + " shut down with the following message"
        print "Could not create new webserver"

    def getStatus(self):
    
        tDat = open("/home/ubuntu/testrun.dat", "a")
        statusOfServers = 0
        for webserver in self.webservers:
            load = webserver.announceStatus()
            if load >= self.maxConnections:
                statusOfServers += 1
            elif load <= self.minConnections:
                statusOfServers -= 1
            tDat.write(str(load) + ' ')
        tDat.write('\n')
        tDat.close()
        print '\n\nThe webmanager thinks the status value is' + str(statusOfServers) + '\n\n'
        return statusOfServers

    def validateStatus(self, statusOfServer):
        if statusOfServer > 0:
            if self.createWebServer():
                print "write creaton to log. SUCSESSFULL!"
                self.setOnCooldown()
            else:
                print "FAILED"
        elif statusOfServer < 0 and self.currentWebservers > 1:
            self.deleteWebServer()
            print "write deletion to log"
            print "SERVER REMOVED"
            self.setOnCooldown()
        else:
            print "None overloaded. NOTHING TO DO!"
            
    def setOnCooldown(self):
        counter = 0
        while counter <= 30:
            print 'The server status is ' + str(self.getStatus())
            sleep(10)
            counter += 10

class webserver:
    ipAddress = None
    hostName = ''
    def __init__(self, hostname):
        print "\n" + hostname + "\n"
        self.hostName = hostname
        try:
 
            image = nova.images.find(name="webserver")
            flavor = nova.flavors.find(name="m1.tiny")
            net = nova.networks.find(label="awtConsulting_net")
            nics = [{'net-id': 'daf055ce-3cbb-4df1-bc9c-9e5058d51b5b',"v4-fixed-ip": ''}]
            instance = nova.servers.create(name=self.hostName, image=image,
                                    flavor=flavor, key_name="josteinkey",
                                    nics=nics)
            print("Sleeping for 5s after create command")
            sleep(5)
            print("List of the VMs")
            print(nova.servers.list())
            novaList = " nova --os-username s177437 --os-password 'cried hang express' --os-tenant-name awtConsulting --os-auth-url 'http://128.39.120.14:5000/v2.0/' list"
            while 1 == 1:
                result = getbash(novaList + " | grep " + hostname + " | awk '{print $12}'").split('=')
                if re.match('\d+\.\d+\.\d+\.\d+', result[-1]):
                    self.ipAddress = result[-1].strip()
                    print 'The server is waiting at IP address {0}.'.format(self.ipAddress)
                    break
            sleep(1)

        
        except:
            print "could not create webserver"
            #WebManager.exception(hostname)
        
        finally:
            print("Execution Completed")
            self.addToLoadbalancer()
            #self.ipAddress = output
            #add host in hammer CLI

    def __del__(self):
        servers_list = nova.servers.list()
        server_del = self.hostName
        server_exists = False
 
        for s in servers_list:
            if s.name == server_del:
                print("This server %s exists" % server_del)
                server_exists = True
                break
        if not server_exists:
            print("server %s does not exist" % server_del)
        else:
            print("deleting server..........")
            nova.servers.delete(s)
            self.removeFromLoadbalancer()
            print("server %s deleted" % server_del)
        print "delete host from Nova"
        print "delete host from hammer CLI"
    
    def addToLoadbalancer(self):
        lConfig = open("/etc/haproxy/haproxy.cfg", "a")
        lConfig.write("server " + str(self.hostName) + " " + str(self.ipAddress) + ":" + "80 check\n")
        lConfig.close()
        runbash('service haproxy restart')
        
    def removeFromLoadbalancer(self):
        lConfig = open("/etc/haproxy/haproxy.cfg", "r") 
        lines = lConfig.readlines()
        lConfig.close()
        lConfig = open("/etc/haproxy/haproxy.cfg","w")
        runbash('service haproxy restart')
        
        for line in lines:
            if line != "server " + str(self.hostName) + " " + str(self.ipAddress) + ":" + "80 check\n":
                lConfig.write(line)
                
        lConfig.close()
        
    def announceStatus(self):
        #result = getbash('netstat -an | grep ' + str(self.ipAddress) + ':80 | wc -l').strip()
        while ('0' not in getbash('nc ' + self.ipAddress + ' 22 < /dev/null; echo $?').split('\n')[1]):
                print "Machine is still booting..."
                sleep(5)


        result = getbash('ssh -o StrictHostKeyChecking=no ubuntu@' + str(self.ipAddress) + ' \'netstat -an | grep ' + str(self.ipAddress) + ':80 | wc -l\'').strip()
        print self.hostName + ' have ' + str(result) + 'connections\n'
        return int(result)

    def exceptionModule(self,string):
        webmanager.exception(string, self.hostname)
        del self

maxwebservers = 5
minWebservers = 2
maxConnections = 100
minConnections = 50

WebManager = webmanager(maxwebservers, minWebservers, maxConnections, minConnections)

while 1 == 1:
    result = webmanager.getStatus(WebManager)
    WebManager.validateStatus(result)
    sleep(5)
