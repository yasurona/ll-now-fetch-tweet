from get_since_id import *
from check_valid_tweet import *
from parse2params import *
from update_since_id import *
import time


def fetch_new_tweets(twitter, sleep_sec, max_api_request_force):
    # dynamodbからsince_idを取得
    since_id = get_since_id()

    url_search = 'https://api.twitter.com/1.1/search/tweets.json'
    url_limit = 'https://api.twitter.com/1.1/application/rate_limit_status.json'
    params = {
        'q': '#lovelive -filter:retweets -filter:replies -from:LLNow_jp -from:lovelivematocha',
        'lang': 'ja',
        'result_type': 'recent',
        'count': 100,
        'since_id': since_id
    }
    res = twitter.get(url_limit)
    contents = res.json()
    max_api_request_real = contents['resources']['search']['/search/tweets']['remaining']
    print('max_api_request: ' + str(max_api_request_real))
    # 手動で定めた上限と実際の上限の小さい方を採用
    max_api_request = min(max_api_request_real, max_api_request_force)

    tweets = []
    for req in range(max_api_request):
        if req != 0 and req % 10 == 0:
            print('{} requested'.format(req))
            # リクエストの間隔を空けるために10回ごとにスリープ
            time.sleep(sleep_sec)

        res = twitter.get(url_search, params=params)
        contents = res.json()
        fetched_tweets = contents['statuses']
        if len(fetched_tweets) == 0:
            break
        for tweet in fetched_tweets:
            if check_valid_tweet(tweet):
                tweets.append(tweet)
        search_metadata = contents['search_metadata']
        next_results = search_metadata['next_results']
        since_id = search_metadata['since_id']
        next_results = next_results.lstrip('?')  # 先頭の?を削除
        params = parse2params(next_results)
        # 崩れるので上書き
        params['q'] = '#lovelive -filter:retweets -filter:replies -from:LLNow_jp -from:lovelivematocha'
        params['since_id'] = since_id

    if len(tweets) == 0:
        latest_tweet = None
    else:
        latest_tweet = tweets[0]

    # since_idを更新
    if latest_tweet is not None:
        next_since_id = latest_tweet['id_str']
        update_since_id(next_since_id)

    return tweets
