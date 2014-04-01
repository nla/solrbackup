solrbackup
==========

Python script for backing up a remote Solr 4 or SolrCloud cluster
via the Solr 4 replication protocol.

Usage
-----

Download all the cores in Solr 4 instance:

    solrbackup.py http://localhost:8080/solr /tmp/mybackup

Download every shard from a SolrCloud cluster:
    
    solrbackup.py --cloud http://anynode:8080/solr /tmp/mybackup

Run it again on the same directory to incrementally update.

TODO
----

* Expire old segments
* Try to get a more consistent snapshot by holding an commitpoint lock across multiple cores
