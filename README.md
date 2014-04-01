solrbackup
==========

Python script for backing up a remote Solr 4 or SolrCloud cluster
via the Solr 4 replication protocol.

Usage
-----

Download all the cores in Solr 4 instance:

    solrbackup.py http://localhost:8080/solr /tmp/mybackup

Download every shard from a SolrCloud cluster (this might be massive):
    
    solrbackup.py --cloud http://anynode:8080/solr /tmp/mybackup

Run it again on the same directory to incrementally update.

TODO
----

* Try to get a more consistent snapshot by holding a commitpoint lock across multiple cores from start
* Option to download from cloud in parallel
* Retry upon failure
* Allow specifying a Zookeeper cluster rather than a URL for cloud downloads
