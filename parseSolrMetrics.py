import json
from itertools import chain, repeat
import sys
import argparse
import aiohttp
import asyncio

parser = argparse.ArgumentParser()
parser.add_argument("-f", help="Specify Solr Metrics JSON File", required=True)
parser.add_argument("-v", help="Specify the major version number for Solr. This will be stored in the version field in the collection", required=True)
parser.add_argument("-c", action='store_true', help="Flag to commit to Solr", required=False)
parser.add_argument("-C", help="Specify the collection as an argument", required=False)
parser.add_argument("-u", help="Specify the URL serving Solr as an argument. Format like this: http://<SOLR_HOST>:<SOLR_PORT> Specify the collection using the -C flag if you use this option", required=False)
parser.add_argument("-n", action='store_true', help="Flag to include Solr.Node Document", required=False)
parser.add_argument("-t", help="Tag all documents with some text", required=False)
args = parser.parse_args()

# global dict mapping of fields to their type
field_type_dict = dict()

# dict mapping field types to field name suffixes
type_to_suffix_dict = {
    "text_general": "_t",
    "string": "_s",
    "pdouble": "_d",
    "plong": "_l",
    "boolean": "_b",
    "text": "_t"
}

def read_file_to_string(file_path):
    f = open(file_path, "r")
    return f.read()


def get_config_map(file_path):
    # read configuration file to map

    return json.loads(read_file_to_string(file_path))


def remove_null_values(this_list):
    # remove all null values from list

    new_list = list()
    for i in this_list:
        if i is not None:
            new_list.append(i)

    return new_list


def first_lower(s):
    # make first letter of string lowercase

    if len(s) == 0:
        return s
    else:
        return s[0].lower() + s[1:]


def grouper(docs_per_submission, doc_objects, pad_value=None):
    # group sets of objects into arrays of chosen length

    return zip(*[chain(doc_objects, repeat(pad_value, docs_per_submission - 1))] * docs_per_submission)


async def async_write_docs(url, docs_list):
    async with aiohttp.ClientSession() as session:
        tasks = list()
        tasks.append(post(session, url, docs_list))
        response = await asyncio.gather(*tasks)


async def post(session, url, data):
    async with session.post(url, data=data, headers={'Content-type': 'application/json'}) as response:
        print(response)
        return await response.text()


def create_docs(map, collection, node, tag, version):
    docs_list = list()

    # take dictionary as map and iterate to create document objects
    for this_key in map.keys():

        name = this_key
        this_map = map[this_key]

        if type(this_map) is dict:
            new_doc = dict()
            if tag != '':
                new_doc['tag' + type_to_suffix_dict[field_type_dict['tag']]] = tag

            new_doc['name' + type_to_suffix_dict[field_type_dict['name']]]             = name
            new_doc['collection' + type_to_suffix_dict[field_type_dict['collection']]] = collection
            new_doc['version' + type_to_suffix_dict[field_type_dict['version']]]       = version

            # add all dict keys to the doc
            for sub_key in this_map.keys():
                # if key is value, don't force type, otherwise use config for type
                if sub_key == 'value':
                    new_doc['value'] = this_map[sub_key]
                else:
                    new_doc[sub_key + type_to_suffix_dict[field_type_dict[sub_key]]]  = this_map[sub_key]

            if node != None:
                new_doc['node' + type_to_suffix_dict[field_type_dict['node']]] = node

            docs_list.append(new_doc)

        else:
            # this is just a single key value pair
            # this_key is the key and this_map is the value
            new_doc = dict()
            if tag != '':
                new_doc['tag' + type_to_suffix_dict[field_type_dict['tag']]] = tag
            new_doc['collection' + type_to_suffix_dict[field_type_dict['collection']]] = collection
            new_doc['version' + type_to_suffix_dict[field_type_dict['version']]]    = version
            new_doc[this_key]       = this_map
            docs_list.append(new_doc)

    return docs_list


def main():
    # get CLI args
    cmd_args        = sys.argv
    flag_commit     = False
    flag_incl_node  = False
    file_path       = str()
    final_docs_list = list()
    tag_value       = str()
    url             = str()
    version         = str()

    configMap       = get_config_map('./config.json')
    hostname               = configMap['hostname']
    protocol               = configMap['protocol']
    port                   = configMap['port']
    destination_collection = configMap['collection']
    docs_per_sub           = configMap['docsPerSubmission']
    field_type_list       = configMap['field_types']
    cli_collection         = str()

    # loop through field types from config and map field name to field type
    for field_map in field_type_list:
        field_type_dict[field_map['name']] = field_map['type']

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
        if cmd_args[opt] == '-t':
            tag_value = cmd_args[opt + 1]
        if cmd_args[opt] == '-u':
            url = cmd_args[opt + 1]
        if cmd_args[opt] == '-C':
            # represents the presence of CLI since destination collection will usually be set by config
            cli_collection         = cmd_args[opt + 1]
            destination_collection = cmd_args[opt + 1]
        if cmd_args[opt] == '-v':
            version = cmd_args[opt + 1]

    # require the user specify a collection if using the url param, or and vice versa
    if (url != '' and cli_collection == '') or (url == '' and cli_collection != ''):
        print('If URL is specified with CL argument, then collection must be set with -C flag, and vice versa')
        print('Exiting')
        exit()

    # flag -c commit overrides config
    if flag_commit:
        commit = True
    else:
        commit = configMap['commit']

    file_json = read_file_to_string(file_path)
    file_obj  = json.loads(file_json)
    # make map of metrics
    file_metrics = file_obj['metrics']
    metrics_keys = file_metrics.keys()

    for key in metrics_keys:
        if len(key.split('.')) > 2:
            collection      = key.split('.')[2]
            node            = key
            new_dict_list   = create_docs(file_metrics[key], collection, node, tag_value, version)
            final_docs_list = final_docs_list + new_dict_list
        else:
            # solr.jvm should maybe be one big document
            if 'solr.jvm' in key:
                solr_jvm_dict        = file_metrics[key]
                solr_jvm_dict['tag' + type_to_suffix_dict[field_type_dict['tag']]] = tag_value
                final_docs_list.append(solr_jvm_dict)
            # Make a flag for it to be created, parse like the others
            # but only if enabled by flag
            elif 'solr.node' in key and flag_incl_node:
                solr_node_dic   = file_metrics[key]
                node_list       = create_docs(solr_node_dic, key, None, tag_value, version)
                final_docs_list = final_docs_list + node_list
            # solr.jetty just skip
            elif 'solr.jetty' in key:
                pass

    # group lists of documents by submit size
    groupedList = list(grouper(docs_per_sub, final_docs_list))

    for group in groupedList:
        # remove any null values from group
        thisGroup = remove_null_values(group)

        # serialize list of docs to json
        thisPayload  = json.dumps(thisGroup)

        if url != '':
            # remove trailing slash if needed
            if url.endswith('/'):
                url = url[:-1]
            this_endpoint = url + '/solr/' + destination_collection + '/update?commit=' + first_lower(str(commit))
        else:
            this_endpoint = protocol + '://' + hostname + ':' + str(
            port) + '/solr/' + destination_collection + '/update?commit=' + first_lower(str(commit))

        # write to Solr with asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(async_write_docs(this_endpoint, thisPayload))


if __name__ == '__main__':
    main()
