from jinja2 import Template
from jinja2 import Environment, PackageLoader, FileSystemLoader

import boto
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.s3.connection import S3Connection
from boto.s3.key import Key

import StringIO
import json
import sys

def write_html(aws_storage_bucket_url, files):
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('index.html')
    rendered = template.render(aws_bucket_url=aws_storage_bucket_url, filenames=files)
    #print rendered
    return rendered

def getBucket(creds):
    try:
        conn = boto.connect_s3(creds['AWS_ACCESS_KEY_ID'], creds['AWS_SECRET_ACCESS_KEY'])
        #print type(conn)
        #print "Successfully connected"
    except Exception as e:
        print "Did not connect {0} {1}".format(e.errno, e.strerror)
        return e
    try:
        bucket_name = creds['AWS_STORAGE_BUCKET_NAME']
        nonexistent = conn.lookup(bucket_name)
        if nonexistent is None:
            print "Bucket doesn't exist {0}".format(bucket_name)
            return
        #else:
        #   print "Bucket exists! {0}".format(bucket_name)
        bucket = conn.get_bucket(bucket_name)
        #print "Successfully got the bucket"
        return bucket
    except Exception as e:
        print type(e)
        print "failed to get the bucket {0} {1}".format(e.errno, e.strerror)
        return e

def getBucketList(creds):
    conn = ''
    bucket = ''
    k = ''
    fp = ''
    try:
        bucket = getBucket(creds)
    except Exception as e:
        return e
    # get the bucket list
    rs = bucket.list()

    for key in rs:
        print key.name
        #print key
    return rs

def writeIndexHtml(creds, indexfile):
    conn = ''
    bucket = ''
    k = ''
    try:
        bucket = getBucket(creds)
    except Exception as e:
        return e
    try:
        # upload the html file
        k = Key(bucket)
        k.key = "index.html"
        #print "Success on setting a key"
    except Exception as e:
        print "failed to set a key"
        return e
    try:
        # upload the html file
        k.set_metadata('Content-Type', 'text/html')
        k.set_contents_from_file(indexfile)
        #print "Success"
    except Exception as e:
        print "failed to upload"
        print type(e)
        print e
        return e

if __name__ == '__main__':
    # Read in the AWS credentials
    fp = open('credentials.json')
    creds = json.load(fp)
    fp.close()

    # retrieve the list of files in the S3 bucket
    filelist = getBucketList(creds)

    # use the html template to write an index.html with "img src=" for each of the
    # files
    rendered = write_html(creds['AWS_STORAGE_BUCKET_URL'], filelist)

    # write out the file locally
    fp = StringIO.StringIO(rendered)   # Wrap object
    f = open('testindex.html', 'w')
    f.write(rendered)
    f.close()

    # Write the file to the S3 bucket
    writeIndexHtml(creds, fp)
