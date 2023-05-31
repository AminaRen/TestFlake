import requests
from nltk.stem import PorterStemmer
import re
from datetime import datetime
import json
from bs4 import BeautifulSoup

def is_good_commit_message(commit_message):

    good_commit_bag_of_words = [
        'fix', 'optimize', 'add', 'test',
        'clean', 'update', 'refactor', 'implement'
        ]
    
    ps = PorterStemmer()
    stemmed_words = set(ps.stem(word) for word in good_commit_bag_of_words)
    
    # Tokenize the commit message into individual words
    words = re.findall(r'\w+', commit_message.lower())
    
    # Check if any stemmed word is present in the commit message
    for word in words:
        if ps.stem(word) in stemmed_words:
            return True
    
    return False

def get_response(endpoint_url, return_json = True):

    TOKEN = 'token'
    API_URL = f'https://api.github.com'
    headers = {'Authorization': f'Token {TOKEN}'}

    if 'https' in endpoint_url:
        url = endpoint_url
    else:
        url = f'{API_URL}/{endpoint_url}'

    response = requests.get(url, headers=headers)

    if response.status_code == 200 and return_json:
        response_json = response.json()
        return response_json
    elif response.status_code == 200:
        return response
    else:
        print(
            f"Не удалось получить информацию по ссылке: {endpoint_url}. Код ошибки: {response.status_code}")
        return None


class User:

    def __init__(self, username):
        self.username = username
        self.registered_days = 0
        self.registration_date = None
        self.languages = {}
        self.good_commit_messages_ratio = 0
        self.repositories_count = 0
        self.projects_count = 0
        self.contributions = 0
        self.stars = 0
        self.forks = 0
        self.get_user_organization()
        self.get_user_followers()
        self.get_user_repositories()
        self.get_user_projects()
        self.get_user_languages()
        self.get_user_registration_date()
        self.get_user_registered_days()
        self.get_user_contributions()
        self.get_user_forks()
        self.get_user_stars()
        # self.get_user_contributed_projects
        # self.get_user_commit_data()

    #  Функция для получения списка организаций, связанных с пользователем GitHub
    def get_user_organization(self):
        endpoint_url = f"users/{self.username}/orgs"
        organizations = get_response(endpoint_url=endpoint_url)
        organizations = [i['login'] for i in organizations]
        self.organizations = organizations


    def get_user_followers(self):
        endpoint_url = f"users/{self.username}/followers"
        self.followers = get_response(endpoint_url=endpoint_url)        

    # Функция для получения всех репозиториев пользователя на GitHub
    def get_user_repositories(self):
        endpoint_url = f"users/{self.username}/repos"
        self.repos = get_response(endpoint_url=endpoint_url)
        self.repositories_count = len(self.repos)

    # Функция для получения проектов пользователя на GitHub
    def get_user_projects(self):
        endpoint_url = f"users/{self.username}/projects"
        self.progects = get_response(endpoint_url=endpoint_url)
        self.projects_count = len(self.progects)

    def get_user_stars(self):
        stars = 0
        for repo in self.repos:
            stars += int(repo["stargazers_count"])
        self.stars = stars

    def get_user_forks(self):
        forks = 0
        for repo in self.repos:
            forks += int(repo["forks"])
        self.forks = forks

    #  Функция для получения словаря языков программирования пользователя GitHub
    #  И количество репозиториев, в которых эти языки были использованы
    def get_user_languages(self):
        languages = {}
        for repo in self.repos:
            endpoint_url = repo["languages_url"]
            languages_in_repo = get_response(endpoint_url=endpoint_url)
            for lang in languages_in_repo:
                if lang in languages:
                    languages[lang] += 1
                else:
                    languages[lang] = 1
        self.languages = languages

    #  Функция для получения даты регистрации пользователя GitHub
    def get_user_registration_date(self):
        endpoint_url = f"users/{self.username}"
        self.registration_date = get_response(endpoint_url=endpoint_url)['created_at']

    #  Функция для получения даты регистрации пользователя GitHub
    def get_user_registered_days(self):
        if self.registration_date == None:
            return None
        reg_date_standard = datetime.strptime(str(self.registration_date), '%Y-%m-%dT%H:%M:%SZ')
        self.registered_days = datetime.now() - reg_date_standard
    
    # Функция для получения вкладов пользователя на GitHub
    def get_user_contributions(self):
        GITHUB_URL = 'https://github.com/'
        url = f'{GITHUB_URL}{self.username}'

        response = get_response(endpoint_url=url, return_json = False)

        bs = BeautifulSoup(response.content, "html.parser")
        total = bs.find('div', {'class': 'js-yearly-contributions'}).findNext('h2')
        contributions = int(total.text.split()[0].replace(',', ''))

        self.contributions = json.dumps(contributions, indent=4)

    def get_user_contributed_projects(self):

        contributed_projects = 0

        for repository in self.repos:
            repo_owner = repository["owner"]["login"]
            repo_name = repository["name"]
            endpoint_url = f'repos/{repo_owner}/{repo_name}/contributors'

            # Получаем информацию о вкладах пользователя в репозиторий
            contributors = get_response(endpoint_url=endpoint_url)

            # Проверяем, есть ли пользователь в списке contributors
            if any(contributor["login"] == self.username for contributor in contributors):
                contributed_projects += 1
        return contributed_projects

    def get_user_commit_data(self):

        total_commits_number = 0
        good_message_commits = 0

        for repo in self.repos:

            repo_name = repo["name"]
            commits_endpoint_url = f"repos/{self.username}/{repo_name}/commits"
            repo_commits = get_response(endpoint_url=commits_endpoint_url)

            # Проходимся по коммитам и анализируем содержимое файлов
            for commit in repo_commits:

                if commit["commit"]["author"]["name"] == self.username:
                    total_commits_number += 1

                    commit_message = commit["commit"]["message"]

                    if is_good_commit_message(commit_message):
                        good_message_commits += 1

                    commit_url = commit["url"]
                    commit_url_response = get_response(endpoint_url=commit_url)

                    commit_files = commit_url_response["files"]
                    
                    for file in commit_files:
                        file_name = file["filename"]

        self.good_commit_messages_ratio = good_message_commits / total_commits_number


user = User('Amina19058')

# print("user.repositories_count", user.repositories_count)
# print("user.projects_count", user.projects_count)
# print("user.stars", user.stars)
# print("user.forks", user.forks)
# print("user.username", user.username)
# print("user.registered_days", user.registered_days)
# print("user.registration_date", user.registration_date)
# print("user.languages", user.languages)
# print("user.good_commit_messages_ratio", user.good_commit_messages_ratio)
# # print("user.contr projects", user.contributed_projects)
# print("user.contributions", user.contributions)
# print("len(user.repos)", len(user.repos))
# print("len(user.progects)", len(user.progects))
# print("user.followers", user.followers)
