#! encoding: utf-8

import tornado.websocket



class SimpleWebSocket(tornado.websocket.WebSocketHandler):
    connections = set()
 
    def open(self):
        self.connections.add(self)
 
    def on_message(self, message):
        [client.write_message(message) for client in self.connections]
 
    def on_close(self):
        self.connections.remove(self)







