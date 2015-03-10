import json
import boto
import urllib2
import StringIO

from multiprocessing import Process, Queue

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream


def uploadUrls(queue, creds):
    while True:
        #print("uploadUrls: queue size is {0}".format(queue.qsize()))
        url = queue.get(True, None)
        upload(url, creds)

def upload(url, creds):
    conn = ''
    bucket = ''
    k = ''
    fp = ''
    filetype = ''

    try:
        aws_access_key_id = creds['AWS_ACCESS_KEY_ID']
        aws_secret_access_key = creds['AWS_SECRET_ACCESS_KEY']
        conn = boto.connect_s3(aws_access_key_id, aws_secret_access_key )
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
    except Exception as e:
        print type(e)
        print "failed to get the bucket {0} {1}".format(e.errno, e.strerror)
        return e
    try:
        k = Key(bucket)
        k.key = url.split('/')[::-1][0]    # In my situation, ids at the end are unique
        filetype = k.key.split('.')[-1]
        if filetype == "jpg":
            filetype = "jpeg"
        if filetype not in ['jpeg','png','tiff', 'gif', 'bmp']:
            print "Skipping filetype {0}".format(filetype)
            return
        #print "Successfully retrieved the key"
    except Exception as e:
        print "failed to get the key"
        print type(e)
        return e
    try:
        file_object = urllib2.urlopen(url)           # 'Like' a file object
        imgfile = file_object.read()
        fp = StringIO.StringIO(imgfile)   # Wrap object
        #print "Successfully downloaded the file {0}".format(url)
    except Exception as e:
        print "failed to download the file"
        print type(e)
        return e
    try:
        filename = "/home/timo/Downloads/extra/" + k.key
        f = open(filename, 'wb')
        f.write(imgfile)
        f.close()
        #print "Successfully saved the file {0}".format(url)
    except Exception as e:
        print "failed to save the file"
        print type(e)
        return e
    try:
        k.set_metadata('Content-Type', 'img/' + filetype)
        k.set_contents_from_file(fp)
        print "Successfully uploaded {0}".format(url)
        return "Success"
    except Exception as e:
        print "failed to upload"
        print type(e)
        return e

#This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):
    def __init__(self, queue):
        self.q = queue
        self.files_uploaded = []

    def on_data(self, data):
        try:
            tweet = json.loads(data)
            #tweets_data.append(tweet)
        except:
            print "error loading json"
            return True
        if u'possibly_sensitive' in tweet and tweet["possibly_sensitive"]:
            return True
        if u'entities' in tweet:
            if u'media' in tweet[u'entities']:
                media_cnt = 0
                for media in tweet[u'entities'][u'media']:
                    if u'media_url_https' in media:
                        # TODO this could load from a file
                        if (media[u'media_url_https'] in self.files_uploaded):
                            print "already added to the queue {0}".format(media[u'media_url_https'])
                        else:
                            print "{0} {1} {2}".format(media_cnt,
                                media[u'media_url_https'], media[u'expanded_url'])
                            # upload(media[u'media_url_https'])
                            # TODO this needs to add more data in -
                            # at least a link back to the original tweet
                            q.put(media[u'media_url_https'])

                            #print("StdOutListener: queue size is {0}".
                            # format(q.qsize()))
                            self.files_uploaded.append(media[u'media_url_https'])
                    else:
                        print "No media_url_https"
                        print tweet[u'entities'][u'media']
                    media_cnt += 1
        else:
            print "No entities"
        if u'extended_entities' in tweet:
            if u'type' in tweet[u'extended_entities']:
                if tweet[u'extended_entities'][u'type'] == 'video':
                    print "There is video {0}".format(tweet[u'extended_entities'][u'video_info']["variants"][0]["url"])
        return True

    def on_error(self, status):
        print status

def twitter_stream(queue, creds):
    #This handles Twitter authetification and the connection to Twitter Streaming API
    l = StdOutListener(queue)
    consumer_key = creds['consumer_key']
    consumer_secret = creds['consumer_secret']
    access_token = creds['access_token']
    access_token_secret = creds['access_token_secret']

    #print "consumer_key {0}".format(consumer_key)
    #print "consumer_secret {0}".format(consumer_secret)
    #print "access_token {0}".format(access_token)
    #print "access_token_secret {0}".format(access_token_secret)
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    stream = Stream(auth, l)

    #This line filter Twitter Streams to capture data by the keywords
    stream.filter(track=[ 'cat', 'kitten' ])

if __name__ == '__main__':

    # Read in the AWS and Twitter credentials
    fp = open('credentials.json')
    creds = json.load(fp)
    fp.close()

    # Create a queue to share URLs between the different processes
    # One process appends URLs to download from and other processes
    # pull off URLs to download. This allows the process montioring
    # the Twitter stream to process updates quickly and lets the slower
    # downloading to happen in other processes
    q = Queue()

    # Start the process to read the twitter stream
    p_twitter = Process(target=twitter_stream, args=(q,creds,))
    p_twitter.start()

    # Start a number of other processes to download the images
    # and upload them in to AWS S3
    p_s3 = []
    for i in range(10):
        p_s3.insert(i, (Process(target=uploadUrls, args=(q,creds,))))
        p_s3[i].start()
        p_s3[i].join()
    p_twitter.join()


