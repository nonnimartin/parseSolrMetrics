# parseSolrMetrics
For use with Python 3

Instructions:

For use with metrics file returned by `curl http://SOLR_HOST:8983/solr/admin/metrics > metrics.json`

You will need to begin by creating a target Collection where the indexed Solr metrics will be stored.

Config file (config.json) will point the software to the IP, port, collection etc. of Solr that is to be updated with the metrics data. This file also holds the mappings between document metric types and the kind of field will be created to store that type of field. You can update config.json to modify this. *Note, it may be necessary to create new entries as versions of Solr may provide metrics not included in the default configuration*

Required flags:

The `-f` flag is _required_ and takes the location of the metrics JSON file to be read.

The `-v` flag is _required_ and stores the version of Solr in a field on all created metrics documents.

Optional flags:

The `-c` flag determines if the commit will be run, and overrides the config.json. It does not take arguments, but is set to true when present.

The `-n` flag switches on and off the creation of Solr.Node documents.

The `-t` flag adds a tag to the "tag" field of all docs created. This can be used to add background or other information to all documents created at a single time.

Example: 

`python3 parseSolrMetrics.py -c -f metrics.json -n`
