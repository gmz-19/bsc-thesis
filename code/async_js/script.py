import os
import requests
import json
import time
import datetime as dt
from datetime import timedelta
import re
import constants
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from git import Repo
import pandas as pd


class Sampling:
    """In this class, individual methods are implemented that were executed for sampling. The sampling process is
    iterative and cannot be performed in one single step. More about this can be found in the paper."""

    def __init__(self):
        """Set date here."""
        self.language = "js"
        self.startDate = dt.date(2013, 1, 1)
        self.endDate = dt.date(2023, 1, 1)
        self.incompleteResult = False
        self.errorCode = "200"
        self.counter = 0
        self.counter2 = 0
        pass

    def requestJsRepos(self):
        """This is the first step of sampling. In this function, all javascript repos that match the characteristics are
        stored in a file. More to the characteristics at the request url."""

        usernames = [constants.USERNAME1, constants.USERNAME2, constants.USERNAME3]
        tokens = [constants.TOKEN1, constants.TOKEN2, constants.TOKEN6, constants.TOKEN7, constants.TOKEN8,
                  constants.TOKEN9]
        current_user = 1
        current_token1 = 2
        current_token2 = 3
        timeout = 0
        repos_counter = 0
        repositories = []
        sampling.setErrorToDefault()

        # Repos are requested per day.
        for single_date in sampling.daterange(self.startDate, self.endDate):
            current_date = single_date.strftime("%Y-%m-%d")

            timeout += 1

            # Check if a timeout is required as the request to GitHub is limited to 5000 per hour.
            # If the intermediate results are saved.
            if sampling.timeOut(timeout, 30):
                print("Write into File ...")
                fileClass.writeToFile(
                    "repos-data/JavaScriptRepos.txt",
                    sampling.repoJsons(
                        None,
                        repos_counter,
                        self.incompleteResult,
                        self.errorCode,
                        repositories,
                    ),
                )

            """ Only 100 results can be returned from GitHub per request, so repos are requested per day.
            Characteristics:
                1. More than 5 stars
                2. No fork
                3. Primary language == language (JavaScript)
                4. Date range 
                5. Filter for asynchronous keywords
            """
            url = f"https://api.github.com/search/repositories?q=stars:>=5+language:{self.language}+created:{current_date}+callback+OR+promise+OR+async+OR+await+OR+fetch+OR+ajax&sort=stars&order=asc&per_page=100"
            repo_by_language_response = requests.get(url, auth=(usernames[current_user], tokens[current_token1]))

            if repo_by_language_response.status_code == 200:
                print(current_date)
                repo_by_lng_response_json = repo_by_language_response.json()

                for responseRepos in repo_by_lng_response_json["items"]:
                    if not responseRepos["fork"]:
                        repos_counter += 1
                        # None values will be added later in sampling
                        repositories.append(
                            sampling.repoKey(
                                None,
                                responseRepos["full_name"],
                                current_date,
                                sampling.requestLanguages(responseRepos["full_name"], usernames[current_user],
                                                          tokens[current_token2]),
                                responseRepos["stargazers_count"],
                                None,
                                None,
                                None,
                            )
                        )

                    if int(sampling.checkApiLimit(usernames[current_user], tokens[current_token1])) < 200:
                        print("Change User and Tokens ...")
                        current_user += 1
                        current_token1 += 2
                        current_token2 += 2
                        if current_user == len(usernames):
                            current_user = 0
                            current_token1 = 0
                            current_token2 = 1
                        print("Current User: ", usernames[current_user])

            else:
                self.errorCode = repo_by_language_response.status_code
                if not self.errorCode == 404:
                    self.incompleteResult = True
                    print(self.errorCode)
                    print("error on repo requests. Current date: " + str(current_date))

        fileClass.writeToFile(
            "repos-data/JavaScriptRepos.txt",
            sampling.repoJsons(
                None, repos_counter, self.incompleteResult, self.errorCode, repositories
            ),
        )

    def setErrorToDefault(self):
        self.incompleteResult = False
        self.errorCode = "200"

    def daterange(self, startDate, endDate):
        """Function that gives the range of the date.

        :param startDate: Date of the first repo to be examined.
        :param endDate: Date of the last repo to be examined.
        :return: list: List of all dates in the given range.
        """
        for n in range(int((endDate - startDate).days)):
            yield startDate + timedelta(n)

    def timeOut(self, currRequestCount, timeOutRequestNumb):
        """If more than the allowed number of requests is exceeded, there will be a one-minute pause.

        :param currRequestCount: Current number of request.
        :param timeOutRequestNumb: If this number is exceeded, a timeout is made.
        :return: boolean: If a timeout is necessary
        """
        if currRequestCount % timeOutRequestNumb == 0:
            self.counter = 0
            time.sleep(10)
            return True

    def requestLanguages(self, repoName, username, token):
        """Function to get all languages used in the repo.

        :param repoName: (boolean): The complete name of a GitHub repository.
        :param username: Username for authentication.
        :param token: Token for authentication.
        :return: Json of the languages used in the repo.
        """
        url = f"https://api.github.com/repos/{repoName}/languages"
        response = requests.get(url, auth=(username, token))

        if response.status_code == 403:
            print("Limit is reached!")

        return response.json()

    def repoKey(self, index, repoFullName, creationDate, languages, stars, issues, commits, constructs):
        return {
            "index": index,
            "repoFullName": repoFullName,
            "creationDate": creationDate,
            "languages": languages,
            "stars": stars,
            "issues": issues,
            "commits": commits,
            "async_constructs": constructs,
        }

    def repoJsons(self, construct, totalCount, incompleteResult, statusCode, repositories):
        return {
            "language": self.language,
            "construct": construct,
            "total_count": totalCount,
            "time_period": "Start date: "
                           + str(self.startDate)
                           + ", end date: "
                           + str(self.endDate),
            "incomplete_results": incompleteResult,
            "status_code": statusCode,
            "repositories": repositories,
        }

    def addVueToJsRepos(self):
        """Adds Vue repo list to JavaScript repo list."""

        print("Adding Vue repos started.")
        vue_repos_list = fileClass.openFile("repos-data/VueRepos.txt")
        vue_repos = vue_repos_list["repositories"]
        js_repos_list = fileClass.openFile("repos-data/JavaScriptRepos.txt")
        js_repos = js_repos_list["repositories"]

        all_repos = js_repos + vue_repos
        all_repos_count = js_repos_list["total_count"] + vue_repos_list["total_count"]

        fileClass.writeToFile(
            "repos-data/JavaScriptRepos.txt",
            sampling.repoJsons(
                None,
                all_repos_count,
                js_repos_list["incomplete_results"],
                js_repos_list["status_code"],
                all_repos,
            ),
        )
        print("Vue repos added.")

    def sortReposByStars(self):
        """Sorts the repo list by stars and gives each repo an id."""

        print("Sorting started.")
        repos_list = fileClass.openFile("repos-data/JavaScriptRepos.txt")
        repos = repos_list["repositories"]

        sorted_repos = sorted(repos, key=lambda repo: repo["stars"], reverse=True)

        index = 1
        time.sleep(15)
        for repo in sorted_repos:
            repo["index"] = index
            index += 1

        fileClass.writeToFile(
            "repos-data/JavaScriptRepos.txt",
            sampling.repoJsons(
                None,
                repos_list["total_count"],
                repos_list["incomplete_results"],
                repos_list["status_code"],
                sorted_repos,
            ),
        )
        print("Sorted.")

    def categorizeJsRepos(self):
        """This is the second step of sampling. In this function, all javascript repos are categorized in three
        asynchronous constructs: callback, promise and async-await."""

        print("Start categorizing.")
        usernames = [constants.USERNAME1, constants.USERNAME2, constants.USERNAME3]
        tokens = [constants.TOKEN1, constants.TOKEN6, constants.TOKEN8]
        current_user = 1
        current_token = 1

        promise_counter = 0
        callback_counter = 0
        async_counter = 0
        uncategorized_counter = 0

        promise_repos = []
        callback_repos = []
        async_repos = []
        uncategorized_repos = []

        # Change file JavaScriptRepos or VueRepos
        repos_list = fileClass.openFile("repos-data/VueRepos.txt")

        for repo in repos_list["repositories"]:
            print("Index: ", repo["index"])
            repo_name = repo["repoFullName"]
            print("RepoName: ", repo_name)
            async_keywords = ["callback", "cb", "fn", "promise", "async"]

            keyword_occur_count = {key: 0 for key in async_keywords}
            total_files = 0

            for keyword in async_keywords:
                if self.language == "vue":
                    url = f"https://api.github.com/search/code?q={keyword}+in:file+language:{self.language}+repo:{repo_name}"
                    response = requests.get(url, auth=(usernames[current_user], tokens[current_token]))
                    time.sleep(6)
                else:
                    url = f"https://api.github.com/search/code?q={keyword}+in:file+language:{self.language}+repo:{repo_name} "
                    response = requests.get(url, auth=(usernames[current_user], tokens[current_token]))
                    time.sleep(6)

                if int(sampling.checkApiLimit(usernames[current_user], tokens[current_token])) < 100:
                    print("Change User and Tokens ...")
                    current_user += 1
                    current_token += 1
                    if current_user == len(usernames):
                        current_user = 0
                    print("Current User: ", usernames[current_user])

                data = response.json()
                # print(f"Error: {response.text}")
                keyword_occur_count[keyword] = data["total_count"]
                total_files += data["total_count"]

            callback_keyword_value = keyword_occur_count["callback"] + keyword_occur_count["cb"] + keyword_occur_count[
                "fn"]
            keyword_occur_count["callback"] = callback_keyword_value
            async_keywords.remove("fn")
            async_keywords.remove("cb")
            keyword_occur_count.pop("fn")
            keyword_occur_count.pop("cb")

            files_count_json = {key: keyword_occur_count[key] for key in async_keywords}
            print(files_count_json)

            if total_files == 0:
                print("No occurrence of keywords.")
                uncategorized_counter += 1
                uncategorized_repos.append(
                    sampling.repoKey(
                        repo["index"],
                        repo_name,
                        repo["creationDate"],
                        repo["languages"],
                        repo["stars"],
                        None,
                        None,
                        files_count_json,
                    )
                )
                fileClass.writeToFile(
                    "repos-data/UncategorizedRepos_Vue.txt",
                    sampling.repoJsons(
                        None,
                        uncategorized_counter,
                        repos_list["incomplete_results"],
                        repos_list["status_code"],
                        uncategorized_repos,
                    ),
                )
                continue

            occur_percentage = {key: round(keyword_occur_count[key] / total_files, 2) for key in async_keywords}
            print(occur_percentage)
            max_keyword = max(occur_percentage, key=occur_percentage.get)
            print("Max Keyword: ", max_keyword)
            # max_value = occur_percentage[max_keyword]

            if (occur_percentage["callback"] > occur_percentage["promise"]) & (
                    occur_percentage["callback"] > occur_percentage["async"]):
                print("Categorized as callback!")
                callback_counter += 1
                callback_repos.append(
                    sampling.repoKey(
                        repo["index"],
                        repo_name,
                        repo["creationDate"],
                        repo["languages"],
                        repo["stars"],
                        None,
                        None,
                        files_count_json,
                    )
                )
            elif (occur_percentage["promise"] > occur_percentage["callback"]) & (
                    occur_percentage["promise"] > occur_percentage["async"]):
                print("Categorized as promise!")
                promise_counter += 1
                promise_repos.append(
                    sampling.repoKey(
                        repo["index"],
                        repo_name,
                        repo["creationDate"],
                        repo["languages"],
                        repo["stars"],
                        None,
                        None,
                        files_count_json,
                    )
                )
            elif (occur_percentage["async"] > occur_percentage["callback"]) & (
                    occur_percentage["async"] > occur_percentage["promise"]):
                print("Categorized as async!")
                async_counter += 1
                async_repos.append(
                    sampling.repoKey(
                        repo["index"],
                        repo_name,
                        repo["creationDate"],
                        repo["languages"],
                        repo["stars"],
                        None,
                        None,
                        files_count_json,
                    )
                )
            else:
                print("Could not categorize ...")
                uncategorized_counter += 1
                uncategorized_repos.append(
                    sampling.repoKey(
                        repo["index"],
                        repo_name,
                        repo["creationDate"],
                        repo["languages"],
                        repo["stars"],
                        None,
                        None,
                        files_count_json,
                    )
                )

            print("Write into Files ... ")
            fileClass.writeToFile(
                "repos-data/CallbackRepos_Vue.txt",
                sampling.repoJsons(
                    async_keywords[0],
                    callback_counter,
                    repos_list["incomplete_results"],
                    repos_list["status_code"],
                    callback_repos,
                ),
            )
            fileClass.writeToFile(
                "repos-data/PromiseRepos_Vue.txt",
                sampling.repoJsons(
                    async_keywords[1],
                    promise_counter,
                    repos_list["incomplete_results"],
                    repos_list["status_code"],
                    promise_repos,
                ),
            )
            fileClass.writeToFile(
                "repos-data/AsyncRepos_Vue.txt",
                sampling.repoJsons(
                    async_keywords[2],
                    async_counter,
                    repos_list["incomplete_results"],
                    repos_list["status_code"],
                    async_repos,
                ),
            )
            fileClass.writeToFile(
                "repos-data/UncategorizedRepos_Vue.txt",
                sampling.repoJsons(
                    None,
                    uncategorized_counter,
                    repos_list["incomplete_results"],
                    repos_list["status_code"],
                    uncategorized_repos,
                ),
            )

        print("Categorized.")

    def deleteNoOccurrenceRepos(self):
        """In this function, all repos without occurrence of asynchronous constructs are deleted."""

        print("Delete Repos.")
        repos_to_keep = []
        keep_counter = 0
        repos_list = fileClass.openFile("repos-data/UncategorizedRepos.txt")

        for repo in repos_list["repositories"]:
            async_constructs = repo["async_constructs"]
            if any(async_constructs.values()):
                keep_counter += 1
                repos_to_keep.append(repo)

        fileClass.writeToFile(
            "repos-data/UncategorizedRepos.txt",
            sampling.repoJsons(
                None,
                keep_counter,
                repos_list["incomplete_results"],
                repos_list["status_code"],
                repos_to_keep,
            ),
        )
        print("Deleted.")

    def reCategorizeUncategorized(self):
        """In this function, all uncategorized repos, which have more than 10 files of occurrences,
        are re-categorized in three asynchronous constructs: callback, promise and async-await.
        Manually add to the Repos.txt."""

        print("Start Re-categorizing.")
        promise_repos = []
        callback_repos = []
        async_repos = []

        # Change file JavaScriptRepos or VueRepos
        repos_list = fileClass.openFile("repos-data/UncategorizedRepos.txt")

        for repo in repos_list["repositories"]:
            constructs = repo["async_constructs"]
            for keyword in constructs:
                if constructs[f"{keyword}"] >= 1:
                    if keyword == "callback":
                        callback_repos.append(repo["index"])
                    elif keyword == "promise":
                        promise_repos.append(repo["index"])
                    elif keyword == "async":
                        async_repos.append(repo["index"])

        print("Callback repos: ", callback_repos)
        print("Promise repos: ", promise_repos)
        print("Async repos: ", async_repos)
        print("Re-categorized.")

    def checkRepoByCharacteristics(self, construct, firstRepoIndex, lastRepoIndex):
        """The third step of sampling. The raw list from the requestRepos function is refined iteratively, sorted out and saved in a second file.

        :param construct: The repo list with this asynchronous construct is examined.
        :param firstRepoIndex: From this index, the raw repo list is refined.
        :param lastRepoIndex: Up to this index, the raw repo list is examined.
        :param numberOfRepos: The size of the repo list after refinement.
        :return:
        """
        fileClass.openFile("repos-data/" + str(construct) + "ReposCharacteristics.txt")
        fileClass.openFile("repos-data/" + str(construct) + "ReposLost.txt")
        repo_list = fileClass.openFile("repos-data/" + str(construct) + "Repos.txt")
        start_index = firstRepoIndex
        start_time = time.time()
        sampling.setErrorToDefault()
        count_repos = 0
        lost_repos = 0
        lost_repos_list = []
        repos_match_characteristics = []
        """
        1 get issues
        1.1 check if there are closed bug-issues and if so save them
        1.2 check if there are unlabeled closed issue and if so check if it is a bug and if so save them

        2 get commits
        2.1 check if there are more than 20 commits
        2.2 check if there are bug-commits and if so save them
        """

        for repo in repo_list["repositories"]:
            if repo["index"] <= lastRepoIndex:
                # Print Info
                print("-----------------------------------------------------------------------------")
                print(str(start_index) + ". Repo " + str(repo["repoFullName"]) + " will be checked")

                # Check first criterion
                print("Get closed issues.")
                closed_bug_issues = sampling.getClosedIssues(repo["repoFullName"])
                print("Finished with issues.")

                if not closed_bug_issues["issues"] == [] and not self.incompleteResult:
                    repo["issues"] = closed_bug_issues
                    # repos_match_characteristics.append(repo)
                else:
                    print("No closed bug issues.")
                    lost_repos += 1
                    start_index += 1
                    lost_repos_list.append(repo)
                    fileClass.writeToFile(
                        "repos-data/" + str(construct) + "ReposLost.txt",
                        sampling.repoJsons(
                            str(construct).lower(),
                            lost_repos,
                            self.incompleteResult,
                            self.errorCode,
                            lost_repos_list,
                        ),
                    )
                    continue

                # Check second criterion
                print("Get bug commits.")
                bug_commits = sampling.getBugCommits(repo["repoFullName"])
                print("Finished with commits.")

                if (
                        not bug_commits["bug_commits"] == []
                        and bug_commits["total_commits"] > 20
                        and not self.incompleteResult
                ):
                    repo["commits"] = bug_commits
                else:
                    print("No bug commits.")
                    lost_repos += 1
                    start_index += 1
                    lost_repos_list.append(repo)
                    fileClass.writeToFile(
                        "repos-data/" + str(construct) + "ReposLost.txt",
                        sampling.repoJsons(
                            str(construct).lower(),
                            lost_repos,
                            self.incompleteResult,
                            self.errorCode,
                            lost_repos_list,
                        ),
                    )
                    continue

                repos_match_characteristics.append(repo)
                count_repos += 1

                fileClass.writeToFile(
                    str("repos-data/") + str(construct) + str("ReposCharacteristics.txt"),
                    sampling.repoJsons(
                        str(construct).lower(),
                        count_repos,
                        self.incompleteResult,
                        self.errorCode,
                        repos_match_characteristics,
                    ),
                )
                fileClass.writeToFile(
                    "ScriptStats.txt",
                    {
                        "checked_repos": "First checked repo: "
                                         + str(firstRepoIndex)
                                         + ", last checkedRepo: "
                                         + str(start_index - 1),
                        "lostRepos": lost_repos,
                        "checkNextIndex": start_index + 1,
                    },
                )
            else:
                print(
                    str(len(repos_match_characteristics["repositories"]))
                    + " Repos found that match the characteristics."
                )
                end_time = time.time()
                print("%5.3f" % (end_time - start_time))
                print("%5.3f".format(end_time - start_time))
                print("{:5.3f}s".format(end_time - start_time))
                fileClass.writeToFile(
                    "ScriptStats.txt",
                    {
                        "checked_repos": "First checked repo: "
                                         + str(firstRepoIndex)
                                         + ", last checkedRepo: "
                                         + str(start_index - 1),
                        "lostRepos": lost_repos,
                        "timeToCheck": "{:5.3f}s".format(end_time - start_time),
                        "checkNextIndex": start_index + 1,
                    },
                )
                break
            start_index += 1

    def getClosedIssues(self, repoName):
        """Iterates through all GitHub issues of a repository.

        Args:
            repoName (string): The complete name of a GitHub repository from which the issues are examined.
        Returns:
            list: json from the issues with all the important information for the study.
        """
        usernames = [constants.USERNAME1, constants.USERNAME2, constants.USERNAME3]
        tokens = [constants.TOKEN, constants.TOKEN6, constants.TOKEN8]
        current_user = 0
        current_token = 0

        page = 0
        issues = []
        total_bug_issues = 0
        total_issues = 0
        sampling.setErrorToDefault()
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Since GitHub only returns the first 100 results per request, multiple requests must be made.
        # Only when all issues have been retrieved, they will be returned.
        while True:
            self.counter2 += 1
            page += 1
            issues_url = f"https://api.github.com/repos/{repoName}/issues?state=closed&per_page=100&page={page}"

            try:
                repo_issues_response = session.get(
                    issues_url, auth=(usernames[current_user], tokens[current_token])
                )
            except session.exceptions.ConnectionError:
                time.sleep(60)
                print("Change User and Tokens ...")
                current_user += 1
                current_token += 1
                if current_user == len(usernames):
                    current_user = 0
                    current_token = 0
                print("Current User: ", usernames[current_user])

            if repo_issues_response.status_code == 200:
                repo_issues_response_json = repo_issues_response.json()
                print("Page: ", page)
                if not (repo_issues_response_json == []):
                    # Iterate through all closed issues
                    for issueKey in repo_issues_response_json:

                        # Closed pull requests will be listed here too, so skip them
                        if "pull_request" in issueKey:
                            continue
                        # Skip issues written in chinese.
                        """if not sampling.checkIfContainsChinese(issueKey["title"]) or sampling.checkIfContainsChinese(issueKey["body"]):
                            print("Chinese found in: ", repoName)
                            continue"""

                        total_issues += 1
                        label = ""
                        text = (
                            issueKey["title"].lower() + issueKey["body"].lower()
                            if issueKey["body"]
                            else issueKey["title"].lower()
                        )

                        # If there are labels
                        if 0 < len(issueKey["labels"]):
                            # If there are more than one label
                            for labelKey in issueKey["labels"]:
                                if "bug" in labelKey["name"].lower():
                                    label = "bug"
                                    total_bug_issues += 1
                                    break
                                # If there are other labels, but in text "bug"
                                """elif sampling.checkIfBug(text):
                                    label = labelKey["name"]
                                    total_bug_issues += 1"""
                        # If there is no label
                        elif len(issueKey["labels"]) == 0:
                            if sampling.checkIfBug(text):
                                label = "unlabeledBug"
                                total_bug_issues += 1

                        if not label == "":
                            issue_comment_info = sampling.requestIssueComments(
                                repoName, issueKey["number"]
                            )
                            issues.append(
                                sampling.issueKey(
                                    issueKey["title"],
                                    issueKey["body"] if issueKey["body"] else "",
                                    label,
                                    issueKey["created_at"],
                                    issueKey["closed_at"],
                                    issue_comment_info[0],
                                    issue_comment_info[1],
                                )
                            )
                else:
                    break
            else:
                if not repo_issues_response.status_code == 404:
                    print(repo_issues_response.status_code)
                    self.incompleteResult = True
                    self.errorCode = repo_issues_response.status_code
                    print("error on issue requests. Current repo: " + str(repoName))

        print("Total bug issues: ", total_bug_issues)
        print("Total issues: ", total_issues)

        return sampling.issuesJson(
            self.incompleteResult, self.errorCode, total_bug_issues, total_issues, issues
        )

    def getBugCommits(self, repoName):
        """This function requests all commits and checks if they address a bug and if so.

        Args:
            repoName (string): The complete name of a GitHub repository from which the commits are examined.
        Returns:
            list: List of all commits with relevant information for the study.
        """
        sampling.setErrorToDefault()
        time_out = 0
        page = 0
        commit_count = 0
        full_commit_count = 0
        commits = []
        count_request = 0
        count422 = 0

        # Since several thousand commits are sometimes examined here,
        # several GitHub tokens are needed to reduce the timeout to zero.
        usernames = [constants.USERNAME1, constants.USERNAME2, constants.USERNAME3]
        tokens = [
            constants.TOKEN2,
            constants.TOKEN7,
            constants.TOKEN9]
        current_user = 2
        current_token = 2

        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Since GitHub only returns the first 100 results per request, multiple requests must be made.
        # Only when all commits have been retrieved, they will be returned.
        while True:
            time_out += 1
            page += 1
            print("Page: ", page)
            # First get all commits
            commit_url = f"https://api.github.com/repos/{repoName}/commits?per_page=100&page={page}"

            if time_out % 80 == 0:
                count_request += 1

            # Since the script can run for a very long time, several attempts have been implemented here in case an error occurs.
            try:
                repo_commit_request = session.get(
                    commit_url, auth=(constants.USERNAME1, tokens[0])
                )

                if repo_commit_request.status_code == 403:
                    print(
                        f"Status code 403. Sleep for 5 mins. Token for first request used (Need to have a look at array index): {count_request % 6}"
                    )
                    time.sleep(30)
                    count_request += 1
                    repo_commit_request = session.get(
                        commit_url, auth=(constants.USERNAME2, tokens[1])
                    )
                    if repo_commit_request.status_code == 403:
                        print(
                            f"Still status code 403. Sleep for another 5 mins. Token for first request used (Need to have a look at array index): {count_request % 6}"
                        )
                        time.sleep(30)
                        count_request += 1
                        repo_commit_request = session.get(
                            commit_url,
                            auth=(constants.USERNAME3, tokens[2]),
                        )
                elif not repo_commit_request.status_code == 200:
                    print(
                        f"Status code {repo_commit_request.status_code}. Sleep for 5 mins and try again. If same error again the script will stop. Token for first request used (Need to have a look at array index): {count_request % 6}"
                    )
                    time.sleep(30)
                    count_request += 1
                    repo_commit_request = session.get(
                        commit_url, auth=(constants.USERNAME1, tokens[0])
                    )

            except session.exceptions.ConnectionError:
                time.sleep(30)
                repo_commit_request = session.get(
                    commit_url, auth=(constants.USERNAME3, tokens[2])
                )

            if repo_commit_request.status_code == 200:
                repo_commit_request_json = repo_commit_request.json()
                print(
                    f'{time.strftime("%d.%m.%Y %H:%M:%S")}: {repo_commit_request.status_code}'
                )

                if not repo_commit_request_json == []:
                    for commit in repo_commit_request_json:
                        full_commit_count += 1

                        message = commit["commit"]["message"]
                        # Second get all files from the commit
                        commit_files_url = f'https://api.github.com/repos/{repoName}/commits/{commit["sha"]}'
                        time_out += 1

                        if time_out % 80 == 0:
                            count_request += 1

                        # Since the script can run for a very long time, several attempts have been implemented here in case an error occurs.
                        try:
                            repo_commit_files_request = session.get(
                                commit_files_url,
                                auth=(usernames[current_user], tokens[current_token]),
                            )

                            if repo_commit_files_request.status_code == 403:
                                print(
                                    f"Status code 403. Sleep for 5 mins. Token for second request used (Need to have a look at array index): {count_request % 6}"
                                )
                                count_request += 1
                                time.sleep(60)
                                print("Change User and Tokens ...")
                                current_user += 1
                                current_token += 1
                                if current_user == len(usernames):
                                    current_user = 0
                                    current_token = 0
                                print("Current User: ", usernames[current_user])
                                repo_commit_files_request = session.get(
                                    commit_files_url,
                                    auth=(usernames[current_user], tokens[current_token]),
                                )

                                if repo_commit_files_request.status_code == 403:
                                    print(
                                        f"Still status code 403. Sleep for another 5 mins. Token for second request used (Need to have a look at array index): {count_request % 6}"
                                    )
                                    time.sleep(60)
                                    count_request += 1
                                    print("Change User and Tokens ...")
                                    current_user += 1
                                    current_token += 1
                                    if current_user == len(usernames):
                                        current_user = 0
                                        current_token = 0
                                    print("Current User: ", usernames[current_user])
                                    repo_commit_files_request = session.get(
                                        commit_files_url,
                                        auth=(usernames[current_user], tokens[current_token]),
                                    )

                            elif not repo_commit_files_request.status_code == 200:
                                print(
                                    f"Status code {repo_commit_request.status_code}. Sleep for 5 mins and try again. If same error again the script will stop. Token for second request used (Need to have a look at array index): {count_request % 6}"
                                )
                                count_request += 1
                                time.sleep(60)
                                print("Change User and Tokens ...")
                                current_user += 1
                                current_token += 1
                                if current_user == len(usernames):
                                    current_user = 0
                                    current_token = 0
                                print("Current User: ", usernames[current_user])
                                repo_commit_files_request = session.get(
                                    commit_files_url,
                                    auth=(usernames[current_user], tokens[current_token]),
                                )

                        except session.exceptions.ConnectionError:
                            time.sleep(300)
                            repo_commit_files_request = session.get(
                                commit_files_url,
                                auth=(usernames[current_user], tokens[current_token]),
                            )
                        print(
                            f'{time.strftime("%d.%m.%Y %H:%M:%S")}: {repo_commit_files_request.status_code}, cur commit to investigate: {full_commit_count}'
                        )

                        binary = repo_commit_files_request.content

                        repo_commit_files = json.loads(binary)

                        time_out += 1
                        if repo_commit_files_request.status_code == 422:
                            print("Skip commit because of 422 status code.")
                            count422 += 1
                            continue
                        bool = False
                        # Check for each commit if it contains a relevant file (.js or .vue)
                        for commitFile in repo_commit_files["files"]:
                            if (
                                    commitFile["filename"].endswith(".js")
                                    or commitFile["filename"].endswith(".cjs")
                                    or commitFile["filename"].endswith(".jsx")
                                    or commitFile["filename"].endswith(".vue")
                            ):
                                if not bool:
                                    commit_count += 1
                                bool = True
                                if sampling.checkIfBug(message):
                                    commits.append(
                                        sampling.bugCommitKey(
                                            message,
                                            commit["commit"]["committer"]["date"],
                                            commit["sha"],
                                        )
                                    )
                                    break
                else:
                    break
            else:
                if not repo_commit_request.status_code == 404:
                    print(repo_commit_request.status_code)
                    self.incompleteResult = True
                    self.errorCode = repo_commit_request.status_code
                    print(
                        "error on commit requests. Current repo: " + str(repoName)
                    )
        print("Total bug commits: ", len(commits))
        print("Total commits: ", commit_count)
        return sampling.commitJson(
            self.incompleteResult,
            self.errorCode,
            len(commits),
            commit_count,
            commits,
        )

    def checkIfContainsChinese(self, string):
        """Checks if a text contains chinese.

        Args:
            string (string): The text which is to be examined.
        Returns:
            boolean: If the text contains chinese
        """
        count_symbols = 0
        # Problem here: Smileys are also reported as chinese
        if re.search("[\u4e00-\u9fff]", string):
            count_symbols += 1
            # contains chinese
        # contains no chinese

        # Returns only true if there are more than 7 symbols
        if count_symbols > 7:
            return True
        else:
            return False

    def checkIfBug(self, text):
        """This function checks if a text contains a bug.

        Args:
            text (string): The text which is to be examined after bug.
        Returns:
            boolean: If the text contains a bug.
        """
        bug_words = ["bug", "fix"]

        if any(bug in text for bug in bug_words):
            return True
        else:
            return False

    def requestIssueComments(self, repoName, issueNumber):
        """Important information for the study is the time stamp of the last comment under the Issues. These are requested here.

        Args:
            repoName (string): The complete name of a GitHub repository from which the issues are examined.
            issueNumber (integer): The unique issue id.
        Returns:
            lsit: List with date and number of comments
        """
        usernames = [constants.USERNAME1, constants.USERNAME2, constants.USERNAME3]
        tokens = [constants.TOKEN, constants.TOKEN6, constants.TOKEN8]
        current_user = 1
        current_token = 1
        page = 0
        total_comments = 0
        last_comment_created = ""
        sampling.setErrorToDefault()

        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Since GitHub only returns the first 100 results per request, multiple requests must be made. Only when all comments have been retrieved, they will be returned.
        while True:
            self.counter += 1
            page += 1
            issues_url = f"https://api.github.com/repos/{repoName}/issues/{issueNumber}/comments?per_page=100&page={page}"

            sampling.timeOut(self.counter, 79)

            try:
                repoIssuesCommentsResponse = session.get(
                    issues_url, auth=(usernames[current_user], tokens[current_token])
                )
            except session.exceptions.ConnectionError:
                time.sleep(60)
                print("Change User and Tokens ...")
                current_user += 1
                current_token += 1
                if current_user == len(usernames):
                    current_user = 0
                    current_token = 0
                print("Current User: ", usernames[current_user])

            if repoIssuesCommentsResponse.status_code == 200:
                repo_issues_comment_response_json = repoIssuesCommentsResponse.json()
                print(repoIssuesCommentsResponse.status_code)
                if not (repo_issues_comment_response_json == []):
                    # Iterate through all comments
                    for commentKey in repo_issues_comment_response_json:
                        total_comments += 1
                        last_comment_created = commentKey["updated_at"]
                else:
                    break

            else:
                if not repoIssuesCommentsResponse.status_code == 404:
                    print(repoIssuesCommentsResponse.status_code)
                    self.incompleteResult = True
                    self.errorCode = repoIssuesCommentsResponse.status_code
                    print("error on issue requests. Current repo: " + str(repoName))
        return [last_comment_created, total_comments]

    def issuesJson(
            self, incompleteResult, statusCode, totalBugIssues, totalIssues, issues
    ):
        return {
            "incomplete_results": incompleteResult,
            "status_code": statusCode,
            "total_bug_issues": totalBugIssues,
            "total_issues": totalIssues,
            "issues": issues,
        }

    def issueKey(
            self, title, description, label, createdAt, closedAt, lastComment, commentCount
    ):
        return {
            "title": title,
            "description": description,
            "label": label,
            "createdAt": createdAt,
            "closedAt": closedAt,
            "lastComment": lastComment,
            "commentCount": commentCount,
        }

    def bugCommitKey(self, message, createdAt, sha):
        return {"message": message, "created_at": createdAt, "sha": sha}

    def commitJson(
            self, incompleteResult, statusCode, totalBugCommits, totalCommits, bugCommits
    ):
        return {
            "incomplete_results": incompleteResult,
            "status_code": statusCode,
            "total_bug_commits": totalBugCommits,
            "total_commits": totalCommits,
            "bug_commits": bugCommits,
        }

    def newIndex(self, construct):
        print("New Indexing started.")
        repos_list = fileClass.openFile("repos-data/" + str(construct) + "Repos.txt")
        repos = repos_list["repositories"]

        sorted_repos = sorted(repos, key=lambda repo: repo["stars"], reverse=True)

        index = 1
        time.sleep(15)
        for repo in sorted_repos:
            repo["index"] = index
            index += 1

        fileClass.writeToFile(
            "repos-data/" + str(construct) + "Repos.txt",
            sampling.repoJsons(
                repos_list["construct"],
                repos_list["total_count"],
                repos_list["incomplete_results"],
                repos_list["status_code"],
                sorted_repos,
            ),
        )

        print("Finished.")

    def checkApiLimit(self, username, token):
        """Check how many requests have already been made this hour.

        :param token: Used token for requests.
        :param username: The username behind the token.
        :return: Rate Limit, Rate Remaining and Rate Reset.
        """
        url = f"https://api.github.com/users/{username}"
        test = requests.head(url, auth=("username", token))
        print("Rate Remaining:", test.headers.get("X-Ratelimit-Remaining"))
        print("Resets in:", test.headers.get("X-Ratelimit-Reset"))

        return test.headers.get("X-Ratelimit-Remaining")


class File:
    """All functions related to the json file are in this class."""

    def __init__(self):
        pass

    def openFile(self, fileName):
        """Opens txt file.

        :param fileName: (string): Complete filename with programming language.
        :return: list: Json of the txt file.
        """
        try:
            with open(fileName, encoding="utf8") as f:
                return json.load(f)
        except:
            print("Create default file")
            fileClass.writeToFile(fileName, None)

    def writeToFile(self, fileName, repoJson):
        """Writes to txt file.

        :param fileName: (string): Complete filename with programming language.
        :param repoJson: (list): The json object to written in the txt file.
        :return:
        """
        with open(fileName, "w", encoding="utf-8") as file:
            json.dump(repoJson, file, ensure_ascii=False, indent=5)

    def deleteFiles(self, files):
        """Remove file from os.

        :param files: (list): List of paths to be deleted.
        """
        for file in files:
            os.remove(file)


class CloneRepo:
    """Automatically downloads the repositories from the list."""

    def __init__(self, construct):
        """
        :param construct: The construct for which the functions from this class should be executed.
        """
        self.curConstruct = construct
        pass

    def cloneRepoFromList(self):
        """Clones all repos from the list."""

        repos = fileClass.openFile("repos-data/" + str(self.curConstruct) + "ReposCharacteristics.txt")

        print("Start with cloning.")
        for repo in repos["repositories"]:
            print("Current repo: " + str(repo["index"]))
            path = ("./git-repos/" + str(self.curConstruct).lower() + "/")

            repo_name = f'{repo["repoFullName"].replace("/", "-")}'
            full_path = path + repo_name
            if not os.path.isdir(full_path):
                try:
                    Repo.clone_from(
                        f'https://github.com/{repo["repoFullName"]}.git', full_path
                    )
                    time.sleep(5)
                except Exception as inst:
                    print("Problem during cloning: " + str(inst))
            else:
                print("Already cloned")
        print("Done cloning.")


# Initialize Sampling object
fileClass = File()
sampling = Sampling()

# 1st step of Sampling: Filter and sort asynchronous JS & Vue repos
# sampling.requestJsRepos()
# sampling.addVueToJsRepos()
# sampling.sortReposByStars()

# 2nd step of Sampling: Categorize repos in async constructs
# sampling.deleteNoOccurrenceRepos()
# sampling.categorizeJsRepos()
# sampling.reCategorizeUncategorized()
# sampling.newIndex("Async")
# sampling.newIndex("Callback")
# sampling.newIndex("Promise")

# 3rd step of Sampling: Filter bug issues and commits
# sampling.checkRepoByCharacteristics("Async", 1, 975)
# sampling.checkRepoByCharacteristics("Callback", 1, 1164)
# sampling.checkRepoByCharacteristics("Promise", 1, 980)
sampling.checkRepoByCharacteristics("Uncategorized", 1, 666)

# Cloning Repos from GitHub
# cloning = CloneRepo("Async")
# cloning = CloneRepo("Callback")
# cloning = CloneRepo("Promise")
# cloning.cloneRepoFromList()

# CHECKING
# sampling.checkApiLimit(constants.USERNAME1, constants.TOKEN1)
# sampling.checkApiLimit(constants.USERNAME2, constants.TOKEN6)
# sampling.checkApiLimit(constants.USERNAME3, constants.TOKEN8)
