import requests
import json
from itertools import chain, repeat
import sys
import argparse
import pprint

parser = argparse.ArgumentParser()
parser.add_argument("-f", help="Specify Solr Metrics JSON File", required=True)
parser.add_argument("-c", action='store_true', help="Flag to commit to Solr", required=False)
args = parser.parse_args()

def read_file_to_string(filePath):
    f = open(filePath, "r")
    return f.read()

def make_new_json_obj(idInt, numFields, startNum):
    # construct json object for update to solr
    thisMap = {}
    thisMap['id'] = idInt

    for field in range(numFields):
        thisMap['x-manyFieldsTest-' + hex(startNum)] = 'x-manyFieldsTest-' + hex(startNum)
        startNum += 1

    idInt += 1

    return thisMap


def get_config_map(filePath):
    # read configuration file to map

    return json.loads(read_file_to_string(filePath))

def update_collection(endpoint, docsJson):
    # create and send http request to desired endpoint

    headersObj = {'content-type': 'application/json'}

    print('sending data to endpoint with ' + str(len(json.loads(docsJson))) + ' documents')

    for i in range(0, 100):
        print('Making request. Trying ' + str(i + 1) + ' times.')
        try:
            r = requests.post(endpoint, data=docsJson, headers=headersObj)
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
            continue
        break

    print("Sent data to endpoint: " + endpoint)
    print("Response status code: " + str(r.status_code))
    print("")
    print("=============================================================")

def grouper(docsPerSubmission, docObjects, padvalue=None):
    # group sets of objects into arrays of chosen length

    return zip(*[chain(docObjects, repeat(padvalue, docsPerSubmission - 1))]* docsPerSubmission)


def main():

    # get CLI args
    cmd_args    = sys.argv
    flag_commit  = False
    file_path    = str()

    # Go through CLI options, where argument value = cmd_args[opt + 1]
    for opt in range(len(cmd_args)):
        # this flag will set commit to true, regardless of config
        if cmd_args[opt] == '-c':
            flag_commit = True
        if cmd_args[opt] == '-f':
            # set file to parse
            file_path = cmd_args[opt + 1]

    file_json    = read_file_to_string(file_path)
    file_obj     = json.loads(file_json)
    # make map of metrics
    file_metrics = file_obj['metrics']
    metrics_keys = file_metrics.keys()
    # maybe make this a dict with a key for each collection
    collections_dict = dict()

    for key in metrics_keys:
        if len(key.split('.')) > 2:
            collection_name = key.split('.')[2]
            # if collection already has entry, add to it, otherwise create
            this_node = {key: file_metrics[key]}
            if collection_name in collections_dict.keys():
                current_nodes_dict                = collections_dict[collection_name]
                current_nodes_dict[key]           = this_node
                collections_dict[collection_name] = current_nodes_dict
            else:
                collections_dict[collection_name] = this_node
        else:
            # these will be non-solr.core nodes, do we want to include these?
            pass

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(collections_dict)


    # for i in metrics_keys:
    #     print(i + ':')
    #     print("")
    #     print(file_metrics[i])

if __name__ == '__main__':
    main()
