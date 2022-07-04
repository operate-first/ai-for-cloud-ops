from operator import contains
import requests
import json
import pprint

origin_link = "http://admin:admin@localhost:5984"

from safety_db import INSECURE, INSECURE_FULL

pp = pprint.PrettyPrinter(indent=4)

# a = {
#     'name' : 'power',
#     'death' : [1,3,4,56,4]
# }

# print(a['death'][1])

# response = requests.get(origin_link + "/_all_dbs")
# pp.pprint(response.content)
# pp.pprint(response.headers)

i = 0
for key, value in INSECURE.items() :
    # print(value)
    if (type(value) != type(list())):
        print(value)
    # print(len(value))
    # print(value[0])
    # if i < 20:
    #     i = i + 1
    #     pp.pprint(value)
    #     break

# pp.pprint(INSECURE_FULL['telnet'])

# j_body = json.loads(body)
# print(json.dumps(j_body, indent=4))