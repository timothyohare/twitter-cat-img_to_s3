# twitter-cat-img_to_s3
Surfs Twitters stream API looking for cat pictures and uploads them to AWS S3

## Getting Cat Images

To run it
1. Add your AWS and Twitter credentials in to the credentials.json file.
2. `$ python ./cat_twitter_img_to_s3.py`
3. It will start one process to read and parse the Twitter stream
4. Once it finds supposed cat pictures (matching 'cat' text in the tweet) it will add the URL to a queue
5. Another process will pull that img URL off the queue, download it in to local memory and upload it to your S3 bucket

Having seperate processes stops the Twitter Stream feed api from blocking
## Creating an index.html of your cat images

It is possible to use your AWS S3 bucket as a static website. Besides some configuration, it needs an index.html file.
The other Python script `python ./create_index.py`
1. connects to your S3 bucket
2. gets a list of files
3. builds an index.html using the list of files to generate <img src=""> tags
4. uploads the index.html up to your S3 bucket
Then you can open your S3 bucket and bammo, you'll see all of your images.

Relys on
- [Tweepy](https://github.com/tweepy/tweepy)
- [Boto](https://github.com/boto/boto)
With inspiration from
- [An Introduction to Text Mining using Twitter Streaming API and Python](http://adilmoujahid.com/posts/2014/07/twitter-analytics/)
