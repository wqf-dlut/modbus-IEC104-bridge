# -*- coding:utf-8 -*-  

'''
Created on 2019.11.14

@author: wqf
'''
import socket
import os
###############################################
#工具函数
###############################################

def heartBeat(strArg):
    '''
        固定位数 16进制字符串自增循环sequence，调用1次+1
    :param strArg: 为16进制字符串,len(strArg)为位数
    :type strArg:String
    
    :return resultStr:为返回值 16进制字符串
    :rtype resultStr:String 为返回值 16进制字符串        
    '''
    lenStr = len(strArg)
    resultStr =''
    maxStr = ''
    minStr = ''
    for i in range(0,lenStr):
        maxStr =maxStr +'f'
        minStr =minStr+'0'
    if int(strArg,16) >= int(maxStr,16) :
        resultStr = minStr
        return resultStr
    resultStr = fillHEX(str(hex(int(strArg,16)+1)).replace('0x','') , lenStr)
    return resultStr
    pass

def heartBeatBin(strArg):
    '''
        固定位数字符串自增循环sequence，调用1次+1
    :param strArg 为2进制字符串,len(strArg)为位数,代表需要自增的字符串
    :type strArg:String
    
    :return resultStr:为自增后的数
    :rtype resultStr:String   返回值 2进制字符串
    '''
    lenStr = len(strArg)
    resultStr =''
    maxStr = ''
    minStr = ''
    for i in range(0,lenStr):
        maxStr =maxStr +'1'
        minStr =minStr+'0'
    if int(strArg,2) >= int(maxStr,2) :
        resultStr = minStr
        return resultStr
    resultStr = fillHEX(d2b((int(strArg,2)+1)) , lenStr)
    return resultStr
    pass



def doConnect(host,port,messageSend):
    '''
用作TCPIP连接连接ip端口，发送数据并接受数据,收到数据后close掉socket
    :param host：连接的ip
    :type host: string类    
    :param port：连接的端口
    :type port:int
    :param messageSend：需要发送的数据
    :type messageSend:string    
    
    :return messageRecv: 发送数据后接受的数据
    :rtype messageRecv:string  
    '''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     optval = struct.pack("ii",1,0)
#     sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, optval )
    sock.settimeout(2.0)#设置超时2s
    try :
#         sock.bind(('127.0.0.1',1123))
        sock.connect((host,port))   #尝试连接

        sock.sendall(hexstr_toSendstr(messageSend))  #发送数据
        #print messageSend
    except :
#         sock.shutdown(2)
#         sock.close()
        return 'SOCKET连接出错'
    try:        
        while 1:
            #接收数据并print
            recv_data = sock.recv(1024)               
            if recv_data:
    #             print"REC",recv_data.encode('hex')
                messageRecv = recv_data.encode('hex')
                break        

#         sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, (1,0))
        sock.shutdown(2)
        sock.close()

        return messageRecv    
    except:
        sock.close()
        return '无回复'  
  
def modbus(slaveID,functionID,startAddress,endAddress,strDATA):
    '''
     modbus控制组装
    :param slaveID：modbus标识符
    :type  slaveID:string
    :param functionID:modbus功能码
    :type  functionID:string
    :param startAddress:起始地址 10进制
    :type  startAddress:string
    :param endAddress:结束地址    10进制
    :type  endAddress:string
    :param strDATA:modbus数据包
    :type  strDATA:string类
    
    :return modbusMessage:组合完整的数据  
    :rtype  modbusMessage:string类
    '''
    modbusIdentifier = '0001'
    modbusProtocol = '0000'
    modbusLength = b2hex(d2b(str(len(strDATA)/2 +7)))
    modbusLength=fillHEX(modbusLength, 4)
    #slaveID
    #functionID
    #startAddress
    modbusAddressCount=b2hex(d2b(str(int(endAddress)+1-int(startAddress))))
    modbusAddressCount=fillHEX(modbusAddressCount, 4)
    modbusByteCount = b2hex(d2b(str(len(strDATA)/2)))
    modbusByteCount= fillHEX(modbusByteCount, 2)
    #strDATA
    modbusMessage = modbusIdentifier+modbusProtocol+modbusLength+slaveID+functionID+fillHEX(b2hex(d2b(startAddress)), 4)+modbusAddressCount+modbusByteCount+strDATA
#     print modbusMessage
    return modbusMessage

def d2hex(arg,lenarg):
    '''
        将arg 10进制数转换为lenarg长度的16进制字符串
    :param arg:需要转换的十进制数
    :type  arg:int
    :param lenarg:长度
    :type  lenarg:int
        
    :return tmp:转换后的16进制字符串
    :rtype  tmp:string类
    '''
    tmp=b2hex(d2b(str(arg)))
    tmp=fillHEX(tmp, lenarg)
    return tmp

def fillHEX(strData,numLen):
    '''
        给X进制数 字符串补全0到 numlen长度,
    :param strData:需要转换的数
    :type  strData:int
    :param numLen:补全后的长度
    :type  numLen:int
        
    :return strData:补全后的字符串
    :rtype  strData:string类
    '''

    while len(strData)< numLen:
        strData= '0'+strData
    return strData


def d2b(str1):   
    '''
        十进制字符串转二进制字符串      int(hex,16)可以吧16进制字符串转10进制    
    :param str1:需要转换的十进制数
    :type  str1:int
        
    :return bi2:转换后的二进制字符串
    :rtype  bi2:string类
    '''  
    bi2=str(bin(int(str1))).replace('0b','')
    return bi2  


def b2hex(str0):
    '''
        二进制字符串转16进制字符串
    :param str0:需要转换的2进制数
    :type  str0:int
        
    :return strw:转换后的16进制字符串
    :rtype  strw:string类
    '''      
    strw=str(hex(int(str0,2))).replace('0x','').upper()
    return strw  

def getBitValue(argStr,argInt,bitCount,bitSum):
    '''
        获得16进制字符串转2进制后第argInt位起共bitCount的值，大端校位
    :param argStr:为16进制字符串
    :type  argStr:string
    :param argInt:10进制数字表示开始位
    :type  argInt:int
    :param bitCount:10进制数字，获取长度
    :type  bitCount:int
    :param bitSum:10进制数字 代表argStr字符串的类型总长度word为8, byte为4
    :type  bitSum:int
        
    :return 返回为二进制字符串
    :rtype  string类
    '''      
    return fillHEX(str(bin(int(argStr,16)))[2:], 4*bitSum)[bitSum*4-argInt-bitCount:bitSum*4-argInt]

def hexstr_toSendstr(a):
    '''
        字符串转为16进制数用于send     改用xx.decode('HEX')......encode('hex')用来recv
    :param a:16进制字符串
    :type  a:string
        
    :return 转换后发送字
    :rtype  hex
    '''          
    return ''.join([chr(int(b, 16)) for b in [a[i:i+2] for i in range(0, len(a), 2)]]) 


def analysisPIDS(messageStr,StaOrTra):
#     输入modbus的data部分分析出pids的控制流
# StaOrTra int:0 表示车站，1表示列车   
    rs =[]
    pidsMessage =''
    for i in range(0,45):
        message0bStr = bin(int(messageStr[i:i+1],16)) #先转10进制再转二进制
        tmp = fillHEX(message0bStr[2:6], 4)
        rs.append(tmp)
    if rs[3][1:2] =='1':
        pidsMessage+='[CLEAR]' 
    else:
        if rs[3][3:4] =='1':pidsMessage+='[Emergency]' 
        if rs[3][2:3] =='1':pidsMessage+='[FULL SCREEN] ' 
        if rs[3][2:3] =='0':pidsMessage+='[ROLL]  '
    
    for i in range(1,41):
        tmp = 7+int((i-1)/4)*4-(i-1)%4
        if StaOrTra ==0:
            if rs[tmp][0:4] <>'0000': pidsMessage+=' Sta['+str(i)+']:'+rs[tmp][0:4]    
        if StaOrTra ==1:
            if rs[tmp][3:4]<>'0':pidsMessage+=' Trn['+str(i*4-3)+'];'
            if rs[tmp][2:3]<>'0':pidsMessage+=' Trn['+str(i*4-2)+'];'
            if rs[tmp][1:2]<>'0':pidsMessage+=' Trn['+str(i*4-1)+'];'
            if rs[tmp][0:1]<>'0':pidsMessage+=' Trn['+str(i*4)+'];' 
            if i >17:
                break                     
    print pidsMessage


def crc16(data,length):
#crc校验 CRC16 CCITT FALSE
# data为 16进制数的list
# length为从头到尾巴的计算数据长度
# 返回值为16进制字符串
    crc = 0xFFFF
    for i in range(0, length):
        crc ^= data[i] << 8
        for j in range(0,8):
            if (crc & 0x8000) > 0:
                crc =(crc << 1) ^ 0x1021
            else:
                crc = crc << 1
    return format((crc & 0xFFFF),'x')       
    
def file_control(arg,file_path):
#文件读取函数
#arg 字符串 r,w之类的
# file_path为文件路径
#返回r的 list
#其他返回文件的对象
    #判断是否存在文件，存在则读取,以前写的函数
    if os.path.exists(file_path):
        account_file = open(file_path, arg)
        MESSAGE =[]
        for i in account_file.readlines():
            MESSAGE.append(i.strip())
    else:
        print('Error: Account file "account.db" is not exit, please check!')
        exit(1)
    if 'r'  in arg:
        account_file.close()
        return MESSAGE 
    else:
        return account_file



class modbusEntity():
    def __init__(self):
        self.wSequence ='0000'
        self.wProtocol ='0000'
        pass

    def senRead(self,bSlaveID,bfunctionID,wStartAddr,wEndAddr):
        '''
            制定问询报文
        :param bSlaveID:modbus 单元标识符
        :type  bSlaveID:string 长度为2的16进制字符串
        :param bfunctionID:modbus 功能码
        :type  bfunctionID:string 长度为2的16进制字符串
        :param wStartAddr:modbus 起始地址
        :type  wStartAddr:string 长度为4的16进制字符串
        :param wEndAddr:modbus 结束地址
        :type  wEndAddr:string 长度为4的16进制字符串
                
        :return tmp:组成好的发送包
        :rtype  tmp:string 16进制字符串
        '''
        wAddressCount=str(hex(int(wEndAddr,16)-int(wStartAddr,16)+1))[2:]
        wAddressCount=fillHEX(wAddressCount, 4)
        tmp = self.wSequence + self.wProtocol+'0006' + bSlaveID +bfunctionID+fillHEX(wStartAddr, 4)+wAddressCount
        self.wSequence = heartBeat(self.wSequence)
        return tmp
        pass    
    
    def sendCtl(self,bSlaveID,bfunctionID,wSetAddr,wSetValue): 
        '''
                制定字控制报文
        :param bSlaveID:modbus 单元标识符
        :type  bSlaveID:string 长度为2的16进制字符串
        :param bfunctionID:modbus 功能码
        :type  bfunctionID:string 长度为2的16进制字符串
        :param wSetAddr:modbus 设置起始地址
        :type  wSetAddr:string 长度为4的16进制字符串
        :param wSetValue:modbus 设置的值
        :type  wSetValue:string 长度为4*n的16进制字符串
                
        :return tmp:组成好的发送包
        :rtype  tmp:string 16进制字符串
        '''

        wAddrCount = len(wSetValue)/4
        wAddrCount = d2hex(wAddrCount, 4) 
        if  int(wAddrCount,16)*2<255:      
            byteLength = d2hex(int(wAddrCount,16)*2, 2) 
        else:
            byteLength = '00'
        wLength = d2hex(len(wSetValue)/2+7, 4) 
        tmp = self.wSequence + self.wProtocol+wLength + bSlaveID +bfunctionID+wSetAddr+wAddrCount+byteLength+wSetValue
        self.wSequence = heartBeat(self.wSequence)
        return tmp
        pass
    
    def anaylyReadRec(self):
        pass
    
    def anaylyCtlRec(self):
        pass    