#!/usr/bin/env python

import json, time, os, struct, zlib, sys, errno
from urllib import urlencode
from urllib2 import urlopen
from contextlib import closing

def getjson(url):
    f = urlopen(url)
    try:
        return json.load(f)
    finally:
        f.close()

def listcores(solr_url):
    return getjson(solr_url + '/admin/cores?action=STATUS&wt=json')['status'].keys()

def clusterstate(solr_url):
    return json.loads(getjson(solr_url + '/zookeeper?detail=true&path=%2Fclusterstate.json')['znode']['data'])

def indexversion(solr_url, core):
    response = getjson(solr_url + '/%s/replication?command=indexversion&wt=json' % core)
    return {'generation': response['generation'], 'indexversion': response['indexversion']}

def filelist(solr_url, core, version):
    return getjson(solr_url + '/%s/replication?command=filelist&wt=json&%s' % (core, urlencode(version)))['filelist']

class FileStream(object):
    def __init__(self, f, use_checksum = False):
        self.f = f
        self.use_checksum = use_checksum

    def __iter__(self):
        return self

    def unpack(self, fmt):
        size = struct.calcsize(fmt)
        buf = self.f.read(size)
        if buf:
            return struct.unpack(fmt, buf)
        else:
            return None

    def next(self):
        size, = self.unpack('>i')
        if size is None or size == 0:
            self.close()
            raise StopIteration
        if self.use_checksum:
            checksum, = self.unpack('>q')
        data = self.f.read(size)
        if len(data) < size:
            self.close()
            raise EOFError('unexpected end of file stream')
        if self.use_checksum:
            calculated = zlib.adler32(data) & 0xffffffff
            if calculated != checksum:
                self.close()
                raise 'checksum mismatch: calculated ' + calculated + ' but expected ' + checksum
        return data

    def close(self):
        self.f.close()

def filestream(solr_url, core, version, file, offset=0, use_checksum=False):
    query = {
        'command': 'filecontent',
        'wt': 'filestream',
        'file': file['name'],
        'offset': offset,
        'checksum': 'true' if use_checksum else 'false',
        'generation': version['generation'],
    }
    f = urlopen('%s/%s/replication?%s' % (solr_url, core, urlencode(query)))
    return FileStream(f, use_checksum=use_checksum)

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def is_complete(path, expected_size):
    try:
        return os.path.getsize(path) >= expected_size
    except OSError as e:
        if e.errno == errno.ENOENT:
            return False
        else:
            raise

def nicesize(bytes):
    if bytes < 1024: return '%dB' % bytes
    if bytes < 1024 * 1024: return '%.2fK' % (bytes / 1024.0)
    if bytes < 1024 * 1024 * 1024: return '%.2fM' % (bytes / 1024.0 / 1024.0)
    return '%.2fG' % (bytes / 1024.0 / 1024.0 / 1024.0)

def download_file(solr_url, core, version, file, destdir, use_checksum=True):
    dest = os.path.join(destdir, file['name'])
    if is_complete(dest, file['size']):
        print 'already got', file['name'], 'skipping'
        return
    print 'fetching', file['name']
    with open(dest, 'a+b') as out:
        out.seek(0, 2)
        offset = out.tell()
        with closing(filestream(solr_url, core, version, file, offset, use_checksum=use_checksum)) as stream:
            for packet in stream:
                out.write(packet)
                print file['name'], nicesize(out.tell()), '/', nicesize(file['size']), '%.2f%%' % (100.0 * out.tell() / file['size'])

def download_cores(solr_url, outdir):
    for core in listcores(solr_url):
        version = indexversion(solr_url, core)
        dest = os.path.join(outdir, core)
        mkdir_p(dest)
        for file in filelist(solr_url, core, version):
            download_file(solr_url, core, version, file, dest)

def download_cloud(solr_url, outdir):
    collections = clusterstate(solr_url)
    print collections
    for colname, coldata in collections.iteritems():
        for shardname, sharddata in coldata['shards'].iteritems():
            replica = sharddata['replicas'].values()[0]
            shard_url = replica['base_url']
            core = replica['core']
            version = indexversion(shard_url, core)
            dest = os.path.join(outdir, colname, shardname)
            mkdir_p(dest)
            for file in filelist(shard_url, core, version):
                download_file(shard_url, core, version, file, dest)

def main():
    cloudmode = False
    if '--cloud' in sys.argv:
        cloudmode = True
        sys.argv.remove('--cloud')

    if len(sys.argv) < 3:
        print 'Usage:', sys.argv[0], '[--cloud] solr_url outdir'
        sys.exit(1)

    solr_url = sys.argv[1].rstrip('/')
    outdir = sys.argv[2]

    if cloudmode:
        download_cloud(solr_url, outdir)
    else:
        download_cores(solr_url, outdir)

if __name__ == '__main__': main()
