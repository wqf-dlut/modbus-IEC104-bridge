# -*- coding:utf-8 -*-  
'''
Created on 2020年4月28日

@author: wqf
'''
import threading
import socket
import time
import IOcontrol.IOcontrol as II
class readStorage():
    def __init__(self,startAddr,endAddr,remoteHost,remotePort,bSlaveID,logger):
        '''
        :param startAddr:读取modbus server的开始地址
        :type startAddr:int
        :param endAddr:读取modbus server的结束地址
        :type endAddr:int
        :param remoteHost:读取modbus server的ip '127.0.0.1'
        :type remoteHost:string
        :param remotePort:读取modbus server的port 502
        :type remotePort:int
        :param bSlaveID:读取modbus server的SLAVE ID '01'
        :type bSlaveID:string
        :param self.dataStorage:用于存储读取的值
        :type self.dataStorage:[STRING]
        '''
        self.logger=logger
        # self.ip_port 连接ISCS的modbus server
        self.ip_port = (remoteHost,remotePort)
        self.client = ''
        self.startAddr = startAddr
        self.endAddr = endAddr
        self.bSlaveID=bSlaveID
        self.modbusEntity1 = II.modbusEntity()
        self.dataStorage = []
        for i in range(startAddr,endAddr+1):
            self.dataStorage.append('0000')        
        thread_list = []
        self.refreshThread = threading.Thread(target=self.getData,args=())
        thread_list.append(self.refreshThread)
        for t in thread_list:
            if not t.isAlive():
                t.setDaemon(False)  # 设置为守护线程false
                t.start()      
#         self.refreshThread.join()
                
    def doConnect(self):
        #获取链接
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try :         
            self.client.connect(self.ip_port)
        except :
            pass
        
        
    def getData(self):
        #建立和ISCS modbus server连接收发数据
        self.doConnect()
        while True :
            try : 
                               
                self.client.send(self.modbusEntity1.senRead(self.bSlaveID, '04', str(hex(self.startAddr))[2:], str(hex(self.endAddr))[2:]).decode('HEX'))
                tmp = self.client.recv(8192).encode('HEX')
                for i in range(0,self.endAddr-self.startAddr+1):
                    self.dataStorage[i]= tmp[4*i+18:4*i+22]
            except socket.error :
                self.logger.info(" socket error,do reconnect ")
                time.sleep(3)
                self.doConnect()   
            except :
                self.logger.info(' other error occur ' )          
                time.sleep(3) 
            time.sleep(1)

    
    def ctlData(self,wSetAddress,wSetValue):
#         给modbus寄存器赋值 word的16进制字符串
        '''
        :param wSetAddr:modbus 设置起始地址
        :type  wSetAddr:string 长度为4的16进制字符串
        :param wSetValue:modbus 设置的值
        :type  wSetValue:string 长度为4*n的16进制字符串
        '''
        try:
            sendMessageTmp = self.modbusEntity1.sendCtl(self.bSlaveID, '10', wSetAddress,wSetValue)
            self.logger.info('send ctl cmd to modbus server:'+sendMessageTmp)
            self.client.send(sendMessageTmp.decode('HEX'))
            tmp = self.client.recv(1024).encode('HEX')
            self.logger.info(' recv from modbus server '+tmp )
        except :
            self.logger.info(' modbus server CTL other error occur ' )
        pass
    
    def debug(self):
        self.logger.info( self.dataStorage)
        pass

