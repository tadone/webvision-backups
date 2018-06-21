#!/usr/bin/env python3

import tkinter as tk
import sys, tweepy, time
from tkinter.scrolledtext import ScrolledText
class GUI(tk.Frame):
    def __init__(self, parent, api, auth): #all the tweet stuff that needs to be started
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.initUI()
        self.api = api
        self.auth = auth
        self.myStream = MyStreamListener(self, self.api)
        self.stream = tweepy.Stream(self.auth, self.myStream)

    def initUI(self): #all the tkinter stuff, still need to learn tkinter layouts to make it look better
        self.tweet_text = tk.Entry()
        self.tweet_text.grid(column=1, row=1, sticky='E')
        self.send_tweet = tk.Button(text='Tweet', command = self.update_tweet)
        self.send_tweet.grid(column=2, row=1)
        self.retweet_text = tk.Entry()
        self.retweet_text.grid(column=1, row=2, sticky='E')
        self.retweet = tk.Button(text='Retweet', command = self.retweet_it)
        self.retweet.grid(column=2, row=2)
        self.timeline = ScrolledText()
        self.timeline.grid(column=0, row=0, rowspan=20)
        self.get_tweets = tk.Button(text='Read Timeline', command = self.start_reading)
        self.get_tweets.grid(column=1, row=3)
        self.stop_tweets = tk.Button(text='Stop Timeline', command = self.stop_reading)
        self.stop_tweets.grid(column=1, row=4)
        self.clear_tweets = tk.Button(text='Clear Chat', command = self.clear_text)
        self.clear_tweets.grid(column=1, row=5)
        self.reply_id = tk.Entry()
        self.reply_id.grid(column=1, row=0)
        self.reply_label = tk.Label(text='Reply ID')
        self.reply_label.grid(column=2, row=0)

    def update_tweet(self): #sending tweets. This part is very straightforward
        msg = self.tweet_text.get()
        tweet_id = self.reply_id.get()
        if len(tweet_id) > 0:
            reply_tweet = self.api.get_status(tweet_id)
            user_name = reply_tweet.user.screen_name
            if len(msg) <= 140:
                #print(msg)
                self.api.update_status(('@%s %s' % (user_name, msg)), in_reply_to_status_id = self.reply_id.get())
                self.tweet_text.delete(0, 'end')
                self.reply_id.delete(0, 'end')
            elif len(msg) > 140: #message box saying tweet too long
                over_msg = len(msg) - 140
                print('Tweet is %s characters too long' % over_msg)
        else:
            if len(msg) <= 140:
                self.api.update_status(msg)
                self.tweet_text.delete(0, 'end')
            elif len(msg) > 140: #message box saying tweet too long
                over_msg = len(msg) - 140
                print('Tweet is %s characters too long' % over_msg)

    def start_reading(self): #start's the stream to print tweets to textbox
        self.stream.userstream(async=True)
        print('Starting reading timeline')

    def stop_reading(self): #disconnects the userstream(). Does not actually quit until it finishes its internal loop
        self.stream.disconnect()
        print('Stopping timeline')

    def clear_text(self): #clear the text box when button is pressed
        self.timeline.delete('1.0', 'end')

    def retweet_it(self):
        tweet_id = self.retweet_text.get()
        self.api.retweet(tweet_id)
        self.retweet_text.delete(0, 'end')

class MyStreamListener(tweepy.StreamListener):
    def __init__(self, parent, api): #I can't figure out a way to make this look better, maybe dump all this stuff into settings?
        self.api = api

    def on_status(self, status): #When a new tweet is received, insert the tweet into the tkinter text box
        new_msg = status._json
        try: #try block is here because tkinter doesn't support some unicode characters, mainly emojis
            prog.timeline.insert('1.0', '@%s: %s  [ID %s] \n' % (new_msg['user']['screen_name'], new_msg['text'],new_msg['id']))
        except:
            print('Unicode Error, discarding tweet.')

    def on_error(self, status):
        print(status)

if __name__ == '__main__':
    #Input tokens and launch
    consumer_key = ''
    consumer_secret = ''
    access_token = ''
    access_secret = ''
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)
    api = tweepy.API(auth)
    root = tk.Tk()
    root.title("Twitter Client")
    prog = GUI(root, api, auth)
    root.mainloop()
