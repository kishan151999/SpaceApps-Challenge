import tweepy
import json
consumer_key = "OmEPl3kMIXnnOCW9p01uu5zRL"
consumer_secret = "tJIju2FXwr0yo5D6k28UvwCFCXZJGjgG9pd8E1dhLOTH2DdRmx"
access_token = "1185686629714784257-KGBkU8hXb63RAhvhriQ0Jv4EBQ4lVS"
access_token_secret = "Fd0kNGQxxll0MrmaJytEMct51XAzRrEVk7MhI9JLMb0Uj"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)


def main():

    """
    <their @> Head to <Name of Hospital>
    <Link for route>
    <embed a picture>
    """


    mention = api.mentions_timeline(1)
    MenDic = json.loads(json.dumps(mention[0]._json))
    splitText = MenDic["text"].split(" ")
    splitText.pop(0)
    theirAt = MenDic["user"]["screen_name"]
    postalCode = "".join(splitText)
    messageID = MenDic["id"]
    message = "@{} Head to us".format(theirAt)
    reply(theirAt, message)


def reply(messageID, message):
    api.update_status(message, messageID)

def tweet(message):
    api.update_status(status=message)

main()


