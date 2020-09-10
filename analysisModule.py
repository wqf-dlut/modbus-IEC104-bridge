# -*- coding:utf-8 -*-  
'''
Created on 2020年4月28日
@author: wqf
'''
import IOcontrol.IOcontrol as II
import readStorage
import Queue
import time
import threading
import logging
from logging.handlers import RotatingFileHandler
class analysisModule():
    def __init__(self,storageClass,RTUNUM,logger,offset):
        '''
        :param self.yxBuffer: 遥信的缓存 索引为对外地址 ， [当前值，对内地址word，对内地址bit]
        :type self.yxBuffer:字典 {int:[string,int,int]}
        :param self.ycBuffer: 遥测的缓存 索引为对外地址  ，[value，对内地址word]
        :type self.ycBuffer:字典 {int:[string,int]}
        '''
        self.logger=logger
        self.clasTag=' classTag-'+str(time.time())[-5:]#设置个独立标签用于log
        yx_path = './py_yxconf.csv'        
        self.yxBuffer={} #使用字典提高查询效率 [当前值，对内地址word，对内地址bit]
        for i in II.file_control('r', yx_path):
            tmp = i.split(',')
            self.yxBuffer[int(tmp[0])]=['0',int(tmp[1])-offset,int(tmp[2])] #[value，对内地址word，对内地址bit]，tmp[0]是对外地址
            
        yc_path = './py_ycconf.csv'
        self.ycBuffer={} #使用字典提高查询效率[value，对内地址word]
        for i in II.file_control('r', yc_path):
            tmp = i.split(',')
            self.ycBuffer[int(tmp[0])] = ['0000',int(tmp[1])-offset] #[value，对内地址word]，tmp[0]是对外地址
        self.storageClass = storageClass
             
        self.sendSequence = '000000000000000'#二进制 15bit
        self.recSequence = '000000000000000'
        self.rtuNum = RTUNUM
        self.sendBuffer = Queue.Queue()
        self.startEnable = False
        #启动轮训storage  
        thread1=threading.Thread(target = self.valueCheck,args=(storageClass,))
        thread1.setDaemon(True)
        thread1.start()
        pass
    
    def analysisMessage(self,recvMessage):
        #分析接受到的报文并做出处理
        #recvMessage是接受到的报文字符串
        if recvMessage[0:2] =='68':#判断起始68H
            apci=['','','','','','']
            asdu=[]
            apci[0]=recvMessage[0:2]#68H起始符
            apci[1]=recvMessage[2:4]#APDU长度
            apci[2]=recvMessage[4:6]#控制域1 1-7 发送序列号L
            apci[3]=recvMessage[6:8]#控制域2 0-7 发送序列号H
            apci[4]=recvMessage[8:10]#控制域3 1-7 接收序列号L
            apci[5]=recvMessage[10:12]#控制域4  0-7 接收序列号H         
            for i in range(0,int(apci[1],16)-4):
                asdu.append(recvMessage[2*(i+6):2*(i+6)+2])                
            if II.getBitValue(apci[2], 0,1,4)=='0':#I帧      控制域1 0bit位为0                         
                self.typeIMethod(apci, asdu)
            elif II.getBitValue(apci[2], 1,1,4)=='0':#s帧 确认用   控制域1 0bit位为1,1bit位为0
                self.typeSMethod()
            else: #u帧 控制域1 0bit位为1,1bit位为1
                self.typeUMethod(apci)
                
    
               
    def typeIMethod(self,apci,asdu):
        #S帧报文处理
#         asdu[0] 类型标识 #0b 标度化遥测 带质量无时标；01 单点遥信；64 总召唤；2d 单点遥控   无时标 ;
#         asdu[1] 可变结构限定词 0-6位为信息体个数 ，7位为是否连续1表示连续
#         asdu[2] 传送原因L 03 突发上传；06 激活；07 激活确认；08 停止激活；09 停止激活确认；0a激活终止；14响应总召唤
#         asdu[3] 传送原因H 默认00
#         asdu[4] 单元公共地址L
#         asdu[5] 单元公共地址H
        recSequence = II.fillHEX(II.d2b(int(apci[3],16)), 8)+II.getBitValue(apci[2], 1, 7, 4) #赋值接受序号
        recSequence = II.heartBeatBin(recSequence)
        self.recSequence = recSequence
        self.rtuNum = asdu[5] +asdu [4]
        
        if asdu[0]=='64':#总召唤
            self.logger.info(self.clasTag+" recv I sum-up")
            #第1步先回复确认S帧
            ctlAtea = II.fillHEX(II.b2hex((recSequence[8:]+'0')),2)+II.fillHEX(II.b2hex(recSequence[0:8]),2)
            self.sendBuffer.put('68040100'+ctlAtea)
            self.logger.info(self.clasTag+" send S sum-up 1-confirm:"+'68040100'+ctlAtea)
            #第2步发送镜像帧
            tmp =self.makeIMessage('64', 0, recSequence, '0007', self.rtuNum, [asdu[6]+asdu[7]+asdu[8]+asdu[9],1])            
            self.sendBuffer.put(tmp)#发送镜像帧
            self.logger.info(self.clasTag+" send I sum-up 2-mirror:"+tmp)
            #第3步，发送遥信遥测数据
            for i in self.dataBodyMake(1, 'yx', []):                                
                tmp =self.makeIMessage('01', 1, recSequence, '0014', asdu[5]+asdu[4], i)                
                self.sendBuffer.put(tmp)
                self.logger.info(self.clasTag+" send I sum-up 3.1-yx:"+tmp)

            for i in self.dataBodyMake(1, 'yc', []):
                tmp =self.makeIMessage('0b', 1, recSequence, '0014', asdu[5]+asdu[4], i)
                self.sendBuffer.put(tmp)
                self.logger.info(self.clasTag+" send I sum-up 3.2-yc:"+tmp)
            #第4步结束总召唤
            endtmp='680E'+II.fillHEX(II.b2hex((self.sendSequence[8:]+'0')),2)+II.fillHEX(II.b2hex(self.sendSequence[0:8]),2)+ctlAtea+'64010a00'+asdu[4]+asdu[5]+'00000014'
            self.sendBuffer.put(endtmp)
            self.startEnable = True
            self.logger.info(self.clasTag+" send I sum-up 4-end:"+endtmp)
            self.startEnable =True
            
        if asdu[0]=='67':#时钟同步
            self.logger.info(self.clasTag+" recv I time-set")
            sendApci2_3 = II.fillHEX(II.b2hex((self.sendSequence[8:]+'0')),2)+II.fillHEX(II.b2hex(self.sendSequence[0:8]),2)#发送序号转为word
            self.sendSequence =  II.heartBeatBin(self.sendSequence)#发送序号+1
            
            sendApci4_5 = II.fillHEX(II.b2hex((recSequence[8:]+'0')),4)+II.fillHEX(II.b2hex(recSequence[0:8]),4)
            tmp ='6814'+sendApci2_3+ sendApci4_5+'67010700'
            for i in range(4,len(asdu)+1):
                tmp = tmp +asdu[i]
            self.sendBuffer.put(tmp)
            #do somthing set time...
            
        if asdu[0].lower()=='2d':#单点遥控   无时标  
            wSetAddress= asdu[7]+asdu[6]
            wSetValue = II.fillHEX(asdu[9],4)
            if II.getBitValue(asdu[9], 7, 1, 4)=='1':
                self.logger.info(self.clasTag+" recv I single_point_set chose,data="+wSetValue)
            if II.getBitValue(asdu[9], 7, 1, 4)=='0':
                self.logger.info(self.clasTag+" recv I single_point_set control,data="+wSetValue)
                self.storageClass.ctlData(wSetAddress,wSetValue)
            tmp =self.makeIMessage('2d', 0, recSequence, '0007', self.rtuNum, [asdu[6]+asdu[7]+asdu[8]+asdu[9],1])
            self.sendBuffer.put(tmp)
            
            
    def makeIMessage(self,typeTag,isSerial ,recSeq,sendReason,rtuNum,dataBody):
        '''  
        制作I帧
        :param typeTag:类型标识  0b 标度化遥测 带质量无时标；01 单点遥信；64 总召唤；2d 单点遥控   无时标 
        :type typeTag：string 16进制字符串
        :param isSerial：表示信息体是否连续 0是不连续，1是连续
        :type  isSerial:int      
        :param recSeq：接受信息的序号
        :type   recSeq ：string 15位2进制字符串 大端    
        :param sendReason：发送原因 03 突发上传；06 激活；07 激活确认；08 停止激活；09 停止激活确认；0a激活终止；14响应总召唤
        :type sendReason：string 4位16进制字符串 大端  
        :param rtuNum：站地址 
        :type  rtuNum：string 4位16进制字符串 大端  
        :param dataBody：信息体及信息体个数
        :type  dataBody：[[STRING,INT],[STRING,INT]]    
        
        :return tmp:合并后的字符串
        :rtype tmp:STRING                 
        '''
        apci = ['','','','','','']
        asdu = ['','','','','','']
        apci[0] = '68'#68H起始符
        
        apci[1] = II.d2hex(len(dataBody[0])/2+10, 2)#APDU长度
        apci[2] = II.fillHEX(II.b2hex((self.sendSequence[8:]+'0')),2)#控制域1 1-7 发送序列号L 0位为0 表示I帧
        apci[3] = II.fillHEX(II.b2hex(self.sendSequence[0:8]),2)#控制域2 0-7 发送序列号H
        self.sendSequence =  II.heartBeatBin(self.sendSequence)
        apci[4] = II.fillHEX(II.b2hex((recSeq[8:]+'0')),2)#控制域3 1-7 接收序列号L 0位为0 表示I帧            
        apci[5] = II.fillHEX(II.b2hex(recSeq[0:8]),2)#控制域4  0-7 接收序列号H         
            
        asdu[0] = typeTag#类型标识
        asdu[1] = II.fillHEX(II.b2hex(str(isSerial)+ II.fillHEX(II.d2b(dataBody[1]), 7)),2)#可变结构限定词 0-6位为信息体个数 ，7位为是否连续1表示连续
        asdu[2] = sendReason[2:4]#传送原因L
        asdu[3] = sendReason[0:2]#传送原因H
        asdu[4] = rtuNum[2:4]#单元公共地址L
        asdu[5] = rtuNum[0:2]#单元公共地址H 
        asdu.append(dataBody[0])
        tmp =''
        for i in apci:
            tmp = tmp + i
        for i in asdu:
            tmp = tmp + i    
        return tmp           
        pass
    def dataBodyMake(self,sumOrChange,yxOryc,tmpChange):
        '''
             生成I帧的asdu的信息体部分        
        :param sumOrChange: 1 代表连续 总召唤一类； 0代表非连续
        :type sumOrChange: String
        :param yxOryc: 'yx'or'yc' 分别代表遥信或遥测
        :type yxOryc: String
        :param tmpChange: 代表变位上传的 列表 E.G [[1,'1'],[对外地址,当前值]]
        :type tmpChange: list
        :return returnBodyList: 返回生成的asdu信息体部分 [[信息体,信息体个数],[信息体,信息体个数].....]
        :rtype returnBodyList:LIST  [STRING,INT]      
        '''
        dataBody = ''
        returnBodyList = []
        infoNumList =[]
        infoNum = 0
        if yxOryc == 'yx':
            if sumOrChange == 1:#总召唤传连续数据
                tmpAddr = II.d2hex(str(sorted(self.yxBuffer)[0]), 4) 
                dataBody = dataBody + tmpAddr[2:4] + tmpAddr[0:2] + '00'
                for i in sorted(self.yxBuffer):                
                    if len(dataBody) >400 or infoNum>120: #超长度时进行分包
                        returnBodyList.append([dataBody,infoNum])
                        infoNum = 0                        
                        tmpAddr = II.d2hex(str(i), 4)
                        dataBody =tmpAddr[2:4] + tmpAddr[0:2] + '00'
                    dataBody = dataBody + II.fillHEX(self.yxBuffer[i][0] , 2)
                    infoNum = infoNum + 1

            if sumOrChange == 0:#变位非连续数据
                for i in tmpChange:
                    if len(dataBody) >400 or infoNum>120:
                        returnBodyList.append([dataBody,infoNum])
                        infoNum = 0                        
                        dataBody =''   
                    tmpAddr = II.d2hex(str(i[0]), 4)
                    dataBody = dataBody + tmpAddr[2:4] + tmpAddr[0:2] + '00'
                    dataBody = dataBody + II.fillHEX(i[1],2)
                    infoNum = infoNum + 1                 
        if yxOryc == 'yc':
            if sumOrChange == 1:#总召唤传连续数据
                tmpAddr = II.d2hex(str(sorted(self.ycBuffer)[0]), 4) 
                dataBody = dataBody + tmpAddr[2:4] + tmpAddr[0:2] + '00'
                for i in sorted(self.ycBuffer):
                    if len(dataBody) >400 or infoNum>120:
                        returnBodyList.append([dataBody,infoNum])
                        infoNum = 0                        
                        tmpAddr = II.d2hex(str(i), 4) 
                        dataBody = tmpAddr[2:4] + tmpAddr[0:2] + '00'  
                    dataBody = dataBody + self.ycBuffer[i][0][2:4] +self.ycBuffer[i][0][0:2]+'00'
                    infoNum = infoNum + 1
                 
            if sumOrChange == 0:#变位非连续数据
                for i in tmpChange:
                    if len(dataBody) >400 or infoNum>120:
                        returnBodyList.append([dataBody,infoNum])
                        infoNum = 0 
                        dataBody =''  
                    tmpAddr = II.d2hex(str(i[0]), 4)
                    tmpVale = II.fillHEX(i[1],4)
                    dataBody = dataBody + tmpAddr[2:4] + tmpAddr[0:2] + '00'
                    dataBody = dataBody + tmpVale[2:4] + tmpVale[0:2] + '00'
                    infoNum = infoNum + 1
                  
        if dataBody !='':
            returnBodyList.append([dataBody,infoNum])
        return returnBodyList   
                
    def typeSMethod(self):
        self.logger.info(self.clasTag+" recv S")
        #S帧报文处理
#         预留重发机制
        pass    
    
    def typeUMethod(self,apci):
        #U帧报文处理
        if II.getBitValue(apci[2], 2,1,4)=='1':#为开启帧
            self.sendBuffer.put('68040B000000')#回复开启确认
            self.sendSequence = '000000000000000'#二进制 15bit
            self.recSequence = '000000000000000'
            self.logger.info(self.clasTag+" recv U messge-start")
        if II.getBitValue(apci[2], 4,1,4)=='1':#为停止帧
            self.sendBuffer.put('680423000000')#回复停止确认
            self.startEnable = False
            self.logger.info(self.clasTag+" recv U messge-stop")
        if II.getBitValue(apci[2], 6,1,4)=='1':#为测试帧
            self.sendBuffer.put('680483000000')#回复测试确认
            self.logger.info(self.clasTag+" recv U messge-test")
        
        
    def valueCheck(self,argreadStorageClass): 
#             轮训argreadStorageClass获取变位值
        while True:
#             self.logger.info( '轮询开始')
            if self.startEnable:
                yxChange=[]
                ycChange=[]
                for i in self.yxBuffer:#遥信数据获取及变位判断
                    tmpStorageVale=argreadStorageClass.dataStorage[int(self.yxBuffer[i][1])]
                    tmpValue = II.getBitValue(tmpStorageVale, int(self.yxBuffer[i][2]), 1, 8)
                    if tmpValue != self.yxBuffer[i][0]: 
                        self.yxBuffer[i][0] =tmpValue
                        yxChange.append([i,self.yxBuffer[i][0]])
                       
                for i in self.ycBuffer:#遥信数据获取及变位判断
                    tmpValue = argreadStorageClass.dataStorage[int(self.ycBuffer[i][1])]
                    if tmpValue != self.ycBuffer[i][0]:
                        self.ycBuffer[i][0] =tmpValue  
                        ycChange.append([i,self.ycBuffer[i][0]])
                if len(yxChange)>0:
                    self.logger.debug(('yx data change:',yxChange))
                if len(ycChange)>0:
                    self.logger.debug(('yx data change:',ycChange))
                for i in self.dataBodyMake(0, 'yx', yxChange):                    
                    tmp = self.makeIMessage('01', 0,self.recSequence, '0003',self.rtuNum , i)                    
                    self.sendBuffer.put(tmp)
                for i in self.dataBodyMake(0, 'yc', ycChange):
                    tmp = self.makeIMessage('0b', 0,self.recSequence, '0003',self.rtuNum , i)
                    self.sendBuffer.put(tmp)                         
            time.sleep(2)

# readStorageClass=readStorage.readStorage(0,800,'127.0.0.1',502)
# time.sleep(5)
# a=analysisModule(readStorageClass,'0001')

