# -*- coding:utf-8 -*-  
'''
Created on 2020年1月7日

@author: wqf
'''
import Queue
import socketserver
import time
import threading
import analysisModule
import readStorage
import logging
from logging.handlers import RotatingFileHandler
#####global parameter######
READSTORAGESTART=1 #modbus服务器读取地址起始
READSTORAGEEND=550 #modbus服务器读取地址结束 
REMOTEHOST='127.0.0.1'#modbus服务器ip
REMOTEPORT=502 #modbus服务器PORT
SLAVEID='01' #读取modbus server的SLAVE ID '01'
TIMEOUT = 30 #超时时间
RTUNUM = '0001'#Iec104子站号
SETLOG =10 #日志级别 INFO = 20 #DEBUG = 10
LOGPATH="./Iec104_modbus.log"
LOGCOUNT=3#循环日志的数量
LOGMAXBYTES=1024 #日志大小
#初始化日志模块
logger = logging.getLogger(__name__)
logger.setLevel(level = SETLOG)
#定义一个RotatingFileHandler，最多备份3个日志文件，每个日志文件最大1K
rHandler = RotatingFileHandler(LOGPATH,maxBytes = LOGMAXBYTES*1024,backupCount = LOGCOUNT)
rHandler.setLevel(SETLOG)
formatter = logging.Formatter('%(asctime)s - [trd - %(thread)d ] - %(levelname)s - %(message)s')
rHandler.setFormatter(formatter) 
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(formatter) 
logger.addHandler(rHandler)
logger.addHandler(console)

#初始化modbus接口程序
readStorageClass=readStorage.readStorage(READSTORAGESTART,READSTORAGEEND,REMOTEHOST,REMOTEPORT,SLAVEID,logger)#存轮询modbus的对象


class IEC104socketIO(socketserver.StreamRequestHandler):
    def __init__(self,request, client_address, server):
        socketserver.StreamRequestHandler.__init__(self,request, client_address, server)
        #用于收发的使能
        self.recEnable=False 
        self.sendEnable=False

    def recvMessage(self,acceptAnalysis):
        #acceptAnalysis handle产生的类用来处理Iec104报文
        logger.info( acceptAnalysis.clasTag+' start recvMessage')
        while self.recEnable:
            try:
                recvData=self.request.recv(2048)
                if not recvData:
                    break
                logger.info(acceptAnalysis.clasTag+" "+self.client_address[0]+":"+str(self.client_address[1])+" "+'recv:'+recvData.encode('hex'))
                acceptAnalysis.analysisMessage(recvData.encode('hex'))
            except Exception as e1:#错误的话就直接关闭连接
                logger.error((self.client_address[0]+":"+str(self.client_address[1])+" "+"recv_error closeSocket",e1))
                self.request.close()
                self.finish()
                break
                
    def sendMessage(self,acceptAnalysis):
        #acceptAnalysis handle产生的类用来处理Iec104报文
        logger.info(acceptAnalysis.clasTag+' start sendMessage')
        while self.sendEnable:
            while not acceptAnalysis.sendBuffer.empty():
                tmpSend=acceptAnalysis.sendBuffer.get()
                logger.info(acceptAnalysis.clasTag+" "+self.client_address[0]+":"+str(self.client_address[1])+" "+'send:'+tmpSend)
                try:
                    self.request.sendall(tmpSend.decode('hex'))
                except Exception as e2:
                    self.request.close()
                    self.finish()
                    logger.error((self.client_address[0]+":"+str(self.client_address[1])+" "+"send msg error closeSocket",e2))
                time.sleep(0.2)

    def handle(self):
        self.request.settimeout(TIMEOUT) #设置超时时间
        try:
            #每次链接生成2线程异步收发
            acceptAnalysis = analysisModule.analysisModule(readStorageClass,RTUNUM,logger,READSTORAGESTART)
            threadSend=threading.Thread(target = self.recvMessage,args=(acceptAnalysis,))
            threadRecv=threading.Thread(target = self.sendMessage,args=(acceptAnalysis,))
            threadRecv.setDaemon(True)
            threadSend.setDaemon(True)
            threadRecv.start()
            threadSend.start()
            threadRecv.join()
            threadSend.join()
        except Exception as e:
            logger.error(e)
            logger.info(('handle error',self.client_address,"disconnect"))
            self.request.close()
            acceptAnalysis=None#释放资源
            self.finish()
        finally:
            logger.info( 'final  request')
#             self.request.close()

    def setup(self):
        self.recEnable=True
        self.sendEnable=True
        logger.info(self.client_address[0]+":"+str(self.client_address[1])+" "+" start connected")
    def finish(self):
        self.recEnable = False
        self.sendEnable = False
        logger.info(self.client_address[0]+":"+str(self.client_address[1])+" "+"disconnected")

if __name__=="__main__":
    
    HOST,PORT = "localhost",2404
    server=socketserver.ThreadingTCPServer((HOST,PORT),IEC104socketIO)
    server.serve_forever()
    
