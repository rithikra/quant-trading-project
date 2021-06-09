import requests
import praw
import pandas as pd

def retrieve_info():
	username = 'tbd'
	# reddit = praw.Reddit(
	# 	client_id="to be replaced",
	# 	client_secret="to be replaced",
	# 	password="password",
	# 	user_agent="testscript for trading",
	# 	username="user",
	# )
	# print(reddit.user.me())
	# reddit.read_only = True










	CLIENT_ID = "hidden"
	SECRET_TOKEN = "hidden"


	# note that CLIENT_ID refers to 'personal use script' and SECRET_TOKEN to 'token'
	auth = requests.auth.HTTPBasicAuth(CLIENT_ID, SECRET_TOKEN)

	with open('pw.txt', 'r') as f:
		pw = f.read()

	# here we pass our login method (password), username, and password
	data = {'grant_type': 'password',
	        'username': username,
	        'password': pw}

	# setup our header info, which gives reddit a brief description of our app
	headers = {'User-Agent': 'MyTrader/0.0.1'}

	# send our request for an OAuth token
	res = requests.post('https://www.reddit.com/api/v1/access_token',
	                    auth=auth, data=data, headers=headers, )

	print(res)

	# convert response to JSON and pull access_token value
	TOKEN = res.json()['access_token']

	# add authorization to our headers dictionary
	headers = {**headers, **{'Authorization': f"bearer {TOKEN}"}}

	# while the token is valid (~2 hours) we just add headers=headers to our requests
	requests.get('https://oauth.reddit.com/api/v1/me', headers=headers)

	#request to get information
	hotPosts = requests.get("https://oauth.reddit.com/r/satoshistreetbets/hot",
                   headers=headers, params = {'limit' : 30})
	risingPosts = requests.get("https://oauth.reddit.com/r/satoshistreetbets/rising",
                   headers=headers, params = {'limit' : 30})

	return hotPosts, risingPosts

def indicator1():
	hotPosts, risingPosts = retrieve_info()
	#print(hotPosts)
	print("RISING POSTS")
	print("")
	print("")
	#print(risingPosts.)

	hotDF = pd.DataFrame()
	risingDF = pd.DataFrame()


	for post in hotPosts.json()['data']['children']:
		#print(post['data']['title'])
		hotDF = hotDF.append({
			'title': post['data']['title'],
			'selftext': post['data']['selftext']
			}, ignore_index = True)

	#print(hotDF)
	hotCountTotal = 0
	for i in range(0,24):
		title = hotDF['title'][i]
		text = hotDF['selftext'][i]
		#print(title)
		#print(text)
		title_count = parsing_count(title)
		text_count = parsing_count(text)
		if title_count or text_count:
			hotCountTotal+=1

	print(hotCountTotal)

	for post in risingPosts.json()['data']['children']:
		#print(post['data']['title'])
		risingDF = risingDF.append({
			'title': post['data']['title'],
			'selftext': post['data']['selftext']
			}, ignore_index = True)

	#print(hotDF)
	risingCountTotal = 0
	for i in range(0,24):
		#print(i)
		title = risingDF['title'][i]
		text = risingDF['selftext'][i]
		#print(title)
		#print(text)
		title_count = parsing_count(title)
		text_count = parsing_count(text)
		if title_count or text_count:
			risingCountTotal+=1

	print(risingCountTotal)

	return risingCountTotal > hotCountTotal

	#parsing_count("TESTING TO SEE HOW IT IS SPLIT")

def parsing_count(current_string):
	current_string = current_string.split(' ')
	for word in current_string:
		#print(word)
		if word.lower() == "btc" or word.lower() == "bitcoin":
			return 1
	return 0


def main():
	indicator1()

if __name__ == "__main__":
	main()
