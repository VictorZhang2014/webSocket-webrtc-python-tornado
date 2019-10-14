import tornado.ioloop
import tornado.web
import tornado.websocket
import os 
import json
from enum import Enum

from EventSourceController import EventSourceDemoController, EventSourceController

from tornado.options import define, options
define("port", default=8100, help="run on the given port", type=int)


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("index.html")




class ProtocolTypes(Enum):
    # 创建会话房间
    createRoom      = 1001  
    # 发送内容
    sendContent     = 1002
    # 发送文件
    sendFile        = 1003


class EchoWebSocket(tornado.websocket.WebSocketHandler):
    allClients = []
    roomClients = []

    def __init__(self, application, request, **kwargs):
        super(EchoWebSocket, self).__init__(application, request, **kwargs)
        self.roomNumber = -1


    def open(self):
        print("WebSocket opened. IP: {}".format(self.request.remote_ip))
        EchoWebSocket.allClients.append(self)
        

    def check_origin(self, origin):
        return True
        # To allow connections from any subdomain of your site, you might do something like:
        # parsed_origin = urllib.parse.urlparse(origin)
        # return parsed_origin.netloc.endswith(".mydomain.com")

    def on_message(self, bytesData):
        # 接收消息
        self.handleMessage(bytesData)
        print("客户端数量: " + str(len(EchoWebSocket.allClients)))
        print("客户端房间数量: " + str(len(EchoWebSocket.roomClients)))


    def on_close(self):
        print("WebSocket closed")
        EchoWebSocket.allClients.remove(self)
        self.removeClientInRoom(self.roomNumber, self)
        print("客户端数量: " + str(len(EchoWebSocket.allClients)))
        print("客户端房间数量: " + str(len(EchoWebSocket.roomClients)))
        print("该房间有{}客户端".format(str(len(EchoWebSocket.roomClients[0]["clients"]))))


    def close(self, code, reason):
        print("Websocket closed, code={}, reason={}", code, reason)


    def handleMessage(self, bytesData):
        # 处理接收到的消息
        message = bytesData # str(bytesData, encoding="utf-8")
        jsonDict = json.loads(message)
        protocol = jsonDict["protocol"]
        roomNumber = jsonDict["roomNumber"]
        userName = jsonDict["userName"]
        content = jsonDict["content"]
        self.roomNumber = roomNumber
        clients = None
        if ProtocolTypes(protocol) == ProtocolTypes.createRoom: # 接收：创建会话房间
            print("创建会话房间")
            clients = self.getConnectedClients(roomNumber)
            print(jsonDict)
        else:
            if ProtocolTypes(protocol) == ProtocolTypes.sendContent: # 接收：发送内容
                print("发送内容")
                clients = self.getConnectedClients(roomNumber)
                print(jsonDict)
            elif ProtocolTypes(protocol) == ProtocolTypes.sendFile: # 接收：发送文件
                print("发送文件")
                clients = self.getConnectedClients(roomNumber)
            # 只要有大于一个用户的房间就可以发消息发给多个客户端了
            if len(clients) > 1:
                # 把消息发给同一个房间的其他用户
                wtmsg = json.dumps(jsonDict)
                for client in clients:
                    # if client != self:  # 不包括自己
                    client.write_message(wtmsg)
        print("该房间号{}有{}客户端".format(roomNumber, len(clients)))


    def getConnectedClients(self, roomNumber):
        # 获取连接房间的实例对象们
        clients = self.getRoomInstance(roomNumber)
        if clients == None:
            clients = self.createRoom(roomNumber, self)
        return clients
    


    def removeClientInRoom(self, roomNumber, client):
        # 在指定房间里删除指定用户  
        for room in EchoWebSocket.roomClients:
            if room["roomNumber"] == roomNumber:
                room["clients"].remove(client)
                break
        

    def getRoomInstance(self, roomNumber):
        # 获取客户端房间连接对象实例
        if len(EchoWebSocket.roomClients) <= 0:
            return None
        roomInstane = None
        for room in EchoWebSocket.roomClients:
            if room["roomNumber"] == roomNumber:
                if self not in room["clients"]:
                    room["clients"].append(self)
                roomInstane = room
                break
        if roomInstane == None:
            return None
        return roomInstane["clients"]


    def createRoom(self, roomNumber, client):
        # 创建聊天房间
        # if len(EchoWebSocket.roomClients) <= 0:
        EchoWebSocket.roomClients.append({"roomNumber" : roomNumber, "clients" : [client]})
        EchoWebSocket.allClients.append(client)
        # else:
        #     foundRoom = False
        #     for room in EchoWebSocket.roomClients:
        #         print("2是否找到相同的房间: r1={}, r2={},".format(room["roomNumber"], roomNumber), room["roomNumber"] == roomNumber)
        #         if room["roomNumber"] == roomNumber:
        #             foundRoom = True
        #             room["clients"].append(client)
        #             break
        #     if not foundRoom:
        #         # 如果还没有这个房间的话，就创建一个
        #         EchoWebSocket.roomClients.append({"roomNumber" : roomNumber, "clients" : [client]})
        return [client]



def make_app():
    settings = dict(
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
    )
    return tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/websocket", EchoWebSocket),
            (r"/eventsourcedemo", EventSourceDemoController),
            (r"/eventsource", EventSourceController)
        ], 
        debug=True,
        **settings
    )

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = make_app()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()#  