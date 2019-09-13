# parseSolrMetrics
For use with Python 3
Config file will point the software to the IP, port, collection etc. of Solr that is to be updated with the metrics data. 

The -c flag determines if the commit will be run, and overrides the config.json

The -n flag switches on and off the creation of Solr.Node documents

The -f flag is required and takes the location of the metrics JSON file to be read

The -t flag adds a tag to the "tag" field of all docs created

Example: 

`python3 parseSolrMetrics.py -c -f metrics.json -n`
