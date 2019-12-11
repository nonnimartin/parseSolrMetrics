# parseSolrMetrics
For use with Python 3

You will need to begin by creating a target Collection where the indexed Solr metrics will be stored.

Config file (config.json) will point the software to the IP, port, collection etc. of Solr that is to be updated with the metrics data. This file also holds the mappings between document metric types and the kind of field will be created to store that type of field. You can update config.json to modify this. *Note, it may be necessary to create new entries as versions of Solr may provide metrics not included in the default configuration*

The `-c` flag determines if the commit will be run, and overrides the config.json. It does not take arguments, but is set to true when present.

The `-n` flag switches on and off the creation of Solr.Node documents.

The `-f` flag is _required_ and takes the location of the metrics JSON file to be read.

The `-t` flag adds a tag to the "tag" field of all docs created. This can be used to add background or other information to all documents created at a single time.

The `-v` flag is required and stores the version of Solr in a field on all created metrics documents.

Example: 

`python3 parseSolrMetrics.py -c -f metrics.json -n`
