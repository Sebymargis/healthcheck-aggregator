import requests
import json
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import settings
import collections
import os
from settings import logging

logger = logging.getLogger(__name__)

health = {}
with open('health_links.txt', 'r') as inf:
    health = eval(inf.read())

dictionary = {'schemaVersion':1, 'name':'Data Platform PROD', 'description':'Testing', 'checks': []}
dictionary_hui = {'schemaVersion':1, 'name':'Data Platform PROD', 'description':'This is HUI', 'checks': []}
dictionary_spoor = {'schemaVersion':1, 'name':'Data Platform PROD', 'description':'This is Spoor', 'checks': []}
dictionary_etl = {'schemaVersion':1, 'name':'Data Platform PROD', 'description':'This is ETL', 'checks': []}



class WebApp(tornado.web.Application):
    background_loop = 60000

    def __init__(self):
        handlers = [(r'/', Index),
                    (r'/etl/__health', HealthCheckETL),
                    (r'/all/__health', HealthCheckAll),
                    (r'/spoor/__health', HealthCheckSpoor),
                    (r'/hui/__health', HealthCheckHUI),]
        tornado_settings = dict(template_path=os.path.join(settings.WEBAPP_PATH, "templates"), debug=settings.DEBUG)
        logging.info('Webservice  Starting')
        tornado.web.Application.__init__(self, handlers, **tornado_settings)
        io_loop = tornado.ioloop.IOLoop.instance()
        logging.info('Webservice  Started')
        self.queue_scheduler = tornado.ioloop.PeriodicCallback(
            self.get_health, self.background_loop, io_loop=io_loop)
        self.queue_scheduler.start()

    def get_health(self):
        dictionary['checks'].clear()
        dictionary_spoor['checks'].clear()
        dictionary_etl['checks'].clear()
        dictionary_hui['checks'].clear()
        for k, v in health.items():
            try:
                app_dict = {'ok': '', 'checkOutput': '', 'panicGuide': '', 'severity': '3', 'businessImpact': '',
                            'technicalSummary': 'For individual checks: {}'.format(v), 'name': '', 'lastUpdated': ''}

                response = requests.get(v)
                data = response.json()
                x = len(data['checks'])  # how many checks we have
                i = 0
                temp_status = []
                temp_updated = []
                while i < x:
                    temp_updated.append(data['checks'][i]['lastUpdated'])
                    temp_status.append(data['checks'][i]['ok'])

                    app_dict['severity'] = data['checks'][i]['severity']
                    app_dict['name'] = k
                    app_dict['panicGuide'] = data['checks'][i]['panicGuide']
                    app_dict['businessImpact'] = data['checks'][i]['businessImpact']
                    app_dict['checkOutput'] = response.status_code
                    app_dict['severity'] = data['checks'][i]['severity']
                    i += 1

                #print('--------------------')
                #print(temp_status)
                severity = 3
                for index, status in enumerate(temp_status):
                    if status is True:
                        app_dict['ok'] = True
                        app_dict['severity'] = severity
                    if status is False:
                        #print('For app {} index {}'.format(k, index))
                        app_dict['ok'] = False
                        if app_dict['severity'] < severity:
                            app_dict['severity'] = severity

                least_recent = temp_updated[0]
                for item in temp_updated:
                    if item < least_recent:
                        #print('Comparing {} with {}. found new least-recent'.format(item, least_recent))
                        least_recent = item
                    #else:
                        #print('Comparing {} with {}. nothing to see here'.format(item, least_recent))
                #print('Least recent is {}'.format(least_recent))
                app_dict['lastUpdated'] = least_recent

                #print('Dictionary for {} is {}'.format(k, app_dict))
                logging.debug('Dictionary for {} is {}'.format(k, app_dict))
                dictionary['checks'].append(app_dict)
                if 'hui' in k.lower():
                    dictionary_hui['checks'].append(app_dict)
                elif 'spoor' in k.lower():
                    dictionary_spoor['checks'].append(app_dict)
                elif 'ingester' or 'validator' or 'transformer' in k.lower():
                    dictionary_etl['checks'].append(app_dict)

            except (requests.ConnectionError, requests.Timeout) as err:
                logging.error(err)
                err_dict = {'ok': '', 'checkOutput': '', 'panicGuide': '', 'severity': '3', 'businessImpact': '',
                            'technicalSummary': '', 'name': '', 'lastUpdated': ''}
                if str(err.errno) == "None":
                    custom_err = "Link not found. Please check the link "
                else:
                    custom_err = str(err.errno)

                err_dict['ok'] = False
                err_dict['severity'] = "1"
                err_dict['checkOutput'] = custom_err
                err_dict['name'] = k
                dictionary['checks'].append(err_dict)

        # print('ETL is {}'.format(dictionary_etl))
        # print('HUI is {}'.format(dictionary_hui))
        # print('Spoor is {}'.format(dictionary_spoor))


class Index(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.render('index.html',
                    title_etl="ETL Healthcheck Aggregator",
                    title_hui="HUI Healthchecks Aggregator",
                    title_spoor="Spoor Healthcheck Aggregator",
                    title_all="All Healthchecks Aggregator")


class HealthCheckAll(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(dictionary))


class HealthCheckETL(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(dictionary))


class HealthCheckHUI(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(dictionary_hui))


class HealthCheckSpoor(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(dictionary_spoor))

if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(WebApp())
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

