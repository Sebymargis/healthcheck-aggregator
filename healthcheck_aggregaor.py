import requests
import json
import tornado.ioloop
import tornado.web


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Content-Type', 'application/json; charset="utf-8"')
        self.render("__health", title="Data Healthcheck")


def make_app():
    return tornado.web.Application([
        (r"/__health", MainHandler)
    ])


health = {}

with open('health_links.txt', 'r') as inf:
    health = eval(inf.read())

dictionary = {'schemaVersion':1, 'name':'Data PROD', 'description':'Testing', 'checks': []}
temp_dict = {}

err_dict = {}
class get_health():
    for k, v in health.items():
        try:
            app_dict = {'ok': '', 'checkOutput': '', 'panicGuide': '', 'severity': '3', 'businessImpact': '',
            'technicalSummary': '', 'name': '', 'lastUpdated': ''}

            response = requests.get(v)
            data = response.json()
            x = len(data['checks'])  # how many checks we have
            i = 0
            while i < x:
                if data['checks'][i]['ok'] is False:
                    app_dict['ok'] = False
                    app_dict['lastUpdated'] = data['checks'][i]['lastUpdated']
                    app_dict['severity'] = data['checks'][i]['severity']
                    app_dict['name'] = k

                    break
                else:
                    app_dict['ok'] = True
                    app_dict['lastUpdated'] = data['checks'][i]['lastUpdated']
                    app_dict['severity'] = data['checks'][i]['severity']
                    app_dict['name'] = k

                app_dict['panicGuide'] = data['checks'][i]['panicGuide']
                app_dict['businessImpact'] = data['checks'][i]['businessImpact']
                app_dict['checkOutput'] = response.status_code
                app_dict['technicalSummary'] = data['checks'][i]['technicalSummary']
                i += 1
            print('Dict for {} is: {}'.format(k, app_dict))
            dictionary['checks'].append(app_dict)

        except (requests.ConnectionError, requests.Timeout) as err:
            err_dict = {'ok': '', 'checkOutput': '', 'panicGuide': '', 'severity': '3', 'businessImpact': '',
            'technicalSummary': '', 'name': '', 'lastUpdated': ''}
            if str(err.errno) == "None":
                custom_err = "Link not found. Please check the link "

            err_dict['ok'] = False
            err_dict['severity'] = "3"
            err_dict['checkOutput'] = custom_err
            err_dict['name'] = k
            dictionary['checks'].append(err_dict)


with open('__health', 'w') as outfile:
    json.dump(dictionary, outfile, sort_keys=True, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    get_health()
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
