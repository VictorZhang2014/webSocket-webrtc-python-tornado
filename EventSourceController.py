#! encoding: utf-8

import tornado.web
import time


class EventSourceDemoController(tornado.web.RequestHandler):

    def __init__(self, *args, **kwargs):
        super(EventSourceDemoController, self).__init__(*args, **kwargs)
        

    def get(self):
        self.render("eventsource.html")



class EventSourceController(tornado.web.RequestHandler):

    counterdown = 0

    def __init__(self, *args, **kwargs):
        super(EventSourceController, self).__init__(*args, **kwargs)
        self.set_header('content-type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')
        self.finished = False
 

    async def publish(self, message):
        """Pushes data to a listener."""
        try:
            self.write('data: {}\n\n'.format(message))
            await self.flush()
        except StreamClosedError:
            self.finished = True


    async def get(self, *args, **kwargs):
        try:
            while not self.finished:
                time.sleep(2)
                EventSourceController.counterdown += 1
                current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) 
                message = "Date time is {}, automatically updated {}".format(current_time, EventSourceController.counterdown)
                await self.publish(message)
        except Exception:
            pass
        finally:
            self.finish()




