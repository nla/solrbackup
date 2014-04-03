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

Getting a consistent snapshot
-----------------------------

Solrbackup uses the Solr replication protocol to get a consistent snapshot
of a particular core.  However there's no guarantee that data is consistent across 
multple cores or shards. If you pass the --reserve option solrbackup will try to snapshot 
each core at close to the same time, rather than waiting for the previous download
to finish.

This is still approximate however.  For a fully consistent backup you'll need to
pause indexing (in your client applications), send a hard commit, start solrbackup
with the --reserve option and then resume indexing (you dont have to wait for it
to finish).  It's a good idea to trigger backups of any other application state
that you need the index to be consistent with (such as an SQL database) during the
same window.

TODO
----

* Option to download from cloud in parallel
* Retry upon failure
* Allow specifying a Zookeeper cluster rather than a URL for cloud downloads
