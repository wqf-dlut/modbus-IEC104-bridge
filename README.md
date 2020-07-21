# modbus-IEC104-bridge
将modbus 的server转换为IEC104的server
python version 2.7
一、转发表配置

Py_yxconf.csv用来配置遥信地址，第一列是对外的IEC104 地址，第二列是ISCS的modbus地址word位，第三列是bit位

Py_ycconf.csv用来配置遥测地址，第一列是对外的IEC104 地址，第二列是ISCS的modbus地址


二、IEC104socketIO.py配置

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

三、启动

进入服务器后cd到软件目录 执行python IEC104socketIO.py即可
