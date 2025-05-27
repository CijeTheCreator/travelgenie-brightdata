
import requests


import requests


def send_tourist_task_to_api():
    url = "http://localhost:5000/chat"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "message": """
Your task is to gather information about things to do for tourists in a specific location.

    Start by searching Reddit for recent and relevant posts, comments, or threads that mention activities, attractions, or recommendations for tourists in the target location.

    Extract the URLs of the most relevant Reddit posts (e.g., from subreddits like r/travel, r/solotravel, r/AskReddit, r/CityName, or any other local subreddits).

    For each URL, retrieve the full page content, including the main text of posts and top comments that describe tourist activities or attractions.

    Additionally, if available and relevant, collect external links mentioned in those Reddit posts that lead to other tourism-related content.

    Summarize the key findings into a concise list of recommended things to do in the location, emphasizing popular activities and unique local experiences mentioned by Reddit users.

    Return the summary along with the source URLs used for the information.
"""
    }

    response = requests.post(url, headers=headers, json=data)

    if response.ok:
        return response.json()
    else:
        response.raise_for_status()


# Example usage
if __name__ == "__main__":
    result = send_tourist_task_to_api()
    print(result)
