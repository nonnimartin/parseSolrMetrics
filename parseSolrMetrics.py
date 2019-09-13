import requests
import json
from itertools import chain, repeat
import sys
import argparse
import pprint

parser = argparse.ArgumentParser()
parser.add_argument("-f", help="Specify Solr Metrics JSON File", required=True)
parser.add_argument("-c", action='store_true', help="Flag to commit to Solr", required=False)
parser.add_argument("-n", action='store_true', help="Flag to include Solr.Node Document", required=False)
args = parser.parse_args()

def read_file_to_string(filePath):
    f = open(filePath, "r")
    return f.read()

def get_config_map(filePath):
    # read configuration file to map

    return json.loads(read_file_to_string(filePath))

def remove_null_values(thisList):
    #remove all null values from list

    newList = list()
    for i in thisList:
        if i is not None:
            newList.append(i)

    return newList

def first_lower(s):
   #make first letter of string lowercase

   if len(s) == 0:
      return s
   else:
      return s[0].lower() + s[1:]

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
    print("")

def grouper(docsPerSubmission, docObjects, padvalue=None):
    # group sets of objects into arrays of chosen length

    return zip(*[chain(docObjects, repeat(padvalue, docsPerSubmission - 1))]* docsPerSubmission)

def create_docs(map, collection, node):

    docs_list = list()

    # take dictionary as map and iterate to create document objects
    for this_key in map.keys():

        name = this_key
        this_map = map[this_key]

        if type(this_map) is dict:
            new_doc = dict()
            new_doc['name']       = name
            new_doc['collection'] = collection

            # add all dict keys to the doc
            for sub_key in this_map.keys():
                new_doc[sub_key] = this_map[sub_key]

            if node != None:
                new_doc['node'] = node

            docs_list.append(new_doc)

        else:
            # this is just a single key value pair
            # this_key is the key and this_map is the value
            new_doc = dict()
            new_doc['collection'] = collection
            new_doc[this_key]     = this_map
            docs_list.append(new_doc)

    return docs_list



def main():

    # get CLI args
    cmd_args        = sys.argv
    flag_commit     = False
    flag_incl_node  = False
    file_path       = str()
    final_docs_list = list()
    configMap = get_config_map('./config.json')

    hostname = configMap['hostname']
    protocol = configMap['protocol']
    port = configMap['port']
    destination_collection = configMap['collection']
    docsPerSub = configMap['docsPerSubmission']

    # Go through CLI options, where argument value = cmd_args[opt + 1]
    for opt in range(len(cmd_args)):
        # this flag will set commit to true, regardless of config
        if cmd_args[opt] == '-c':
            flag_commit = True
        if cmd_args[opt] == '-f':
            # set file to parse
            file_path = cmd_args[opt + 1]
        if cmd_args[opt] == '-n':
            # set to include Solr.node
            flag_incl_node = True

    #flag -c commit overrides config
    if flag_commit:
        commit = True
    else:
        commit = configMap['commit']

    file_json    = read_file_to_string(file_path)
    file_obj     = json.loads(file_json)
    # make map of metrics
    file_metrics = file_obj['metrics']
    metrics_keys = file_metrics.keys()

    for key in metrics_keys:
        if len(key.split('.')) > 2:
            collection = key.split('.')[2]
            node       = key
            new_dict_list = create_docs(file_metrics[key], collection, node)
            final_docs_list = final_docs_list + new_dict_list
        else:
            # solr.jvm should maybe be one big document
            if 'solr.jvm' in key:
                solr_jvm_dict = file_metrics[key]
                final_docs_list.append(solr_jvm_dict)
            # Make a flag for it to be created, parse like the others
            # but only if enabled by flag
            elif 'solr.node' in key and flag_incl_node:
                solr_node_dic = file_metrics[key]
                node_list = create_docs(solr_node_dic, key, None)
                final_docs_list = final_docs_list + node_list
            # solr.jetty just skip
            elif 'solr.jetty' in key:
                pass

    #group lists of documents by submit size
    groupedList = list(grouper(docsPerSub, final_docs_list))

    for group in groupedList:
        #remove any null values from group
        thisGroup = remove_null_values(group)

        #serialize list of docs to json
        thisPayload  = json.dumps(thisGroup)
        thisEndpoint = protocol + '://' + hostname + ':' + str(port) + '/solr/' + destination_collection + '/update?commit=' + first_lower(str(commit))
        #iterate progress bar
        update_collection(thisEndpoint, thisPayload)


if __name__ == '__main__':
    main()
