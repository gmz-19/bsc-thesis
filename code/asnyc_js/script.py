import os
import requests
import json
import re
import time
import calendar
import datetime as dt
from datetime import timedelta
import constants
import pandas as pd


class Sampling:
    """In this class, individual methods are implemented that were executed for sampling. The sampling process is
    iterative and cannot be performed in one single step. More about this can be found in the paper."""

    def __init__(self, language):
        """Set date here.
        Args:
            language (string): The programming language for which the functions from this class should be executed.
        """
        self.language = language
        self.startDate = dt.date(2013, 1, 1)
        self.endDate = dt.date(2023, 1, 1)
        self.incompleteResult = False
        self.errorCode = "200"
        self.counter = 0
        self.counter2 = 0
        pass

    def requestRepos(self):
        """This is the first step of sampling. In this function, all repos that match the characteristics are stored
        in a file. More to the characteristics at the request url."""

        timeOut = 0
        reposCounter = 0
        repositories = []
        sampling.setErrorToDefault()

        # Repos are requested per day.
        for single_date in sampling.daterange(self.startDate, self.endDate):
            currentDate = single_date.strftime("%Y-%m-%d")

            timeOut += 1

            # Check if we need a timeout because of the low request limit of 5000 per hour to GitHub. If the intermediate results are saved.
            if sampling.timeOut(timeOut, 30):
                fileClass.writeToFile(
                    str(self.language) + "Repos.txt",
                    sampling.repoJsons(
                        reposCounter,
                        self.incompleteResult,
                        self.errorCode,
                        repositories,
                    ),
                )

            """ Only 100 results can be returned from GitHub per request, so repos are requested per day.
            Characteristics:
                1. More than 5 stars
                2. No fork
                3. Primary language == language
                4. Date range
            """
            url = f"https://api.github.com/search/repositories?q=stars:>=5+language:{self.language}+created:{currentDate}+callback+OR+promise+OR+async+OR+await&sort=stars&order=asc&per_page=100"
            repoByLanguageResponse = requests.get(
                url, auth=("gmz-19", constants.TOKEN3)
            )

            if repoByLanguageResponse.status_code == 200:
                print(currentDate)
                repoByLanguageResponseJson = repoByLanguageResponse.json()

                for responseRepos in repoByLanguageResponseJson["items"]:
                    if not responseRepos["fork"]:
                        reposCounter += 1
                        # None values will be added later in sampling
                        repositories.append(
                            sampling.repoKey(
                                None,
                                responseRepos["full_name"],
                                currentDate,
                                sampling.requestLanguages(responseRepos["full_name"]),
                                responseRepos["stargazers_count"],
                                None,
                                None,
                            )
                        )

            else:
                self.errorCode = repoByLanguageResponse.status_code
                if not self.errorCode == 404:
                    self.incompleteResult = True
                    print(self.errorCode)
                    print("error on repo requests. Current date: " + str(currentDate))

        fileClass.writeToFile(
            str(self.language) + "Repos.txt",
            sampling.repoJsons(
                reposCounter, self.incompleteResult, self.errorCode, repositories
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
            time.sleep(60)
            return True

    def repoKey(self, index, repoFullName, creationDate, languages, stars, issues, commits, asyncFiles):
        return {
            "index": index,
            "repoFullName": repoFullName,
            "creationDate": creationDate,
            "languages": languages,
            "stars": stars,
            "issues": issues,
            "commits": commits,
            "async_files_count": asyncFiles,
        }

    def requestLanguages(self, repoName):
        """Function to get all languages used in the repo.

        :param repoName: (boolean): The complete name of a GitHub repository.
        :return: Json of the languages used in the repo.
        """
        url = f"https://api.github.com/repos/{repoName}/languages"

        return requests.get(url, auth=("gmz-19", constants.TOKEN3)).json()

    def repoJsons(self, totalCount, incompleteResult, statusCode, repositories):
        return {
            "language": self.language,
            "total_count": totalCount,
            "time_period": "Start date: "
                           + str(self.startDate)
                           + ", end date: "
                           + str(self.endDate),
            "incomplete_results": incompleteResult,
            "status_code": statusCode,
            "repositories": repositories,
        }

    def checkApiLimit(self, username):
        """Check how many requests have already been made this hour. Change token number in function.

        :param username: The username behind the token.
        :return: Rate Limit, Rate Remaining and Rate Reset
        """
        url = f"https://api.github.com/users/{username}"
        test = requests.head(url, auth=("username", constants.TOKEN3))
        print("Rate Limit:", test.headers.get("X-RateLimit-Limit'"))
        print("Rate Remaining:", test.headers.get("X-Ratelimit-Remaining"))
        print("Resets in:", test.headers.get("X-Ratelimit-Reset"))

    def sortReposByStars(self):
        """Sorts the repo list by stars and gives each repo an id."""
        print("started")
        reposList = fileClass.openFile(str(self.language) + "Repos.txt")
        repos = reposList["repositories"]

        sortedRepos = sorted(repos, key=lambda repo: repo["stars"], reverse=True)

        index = 1
        time.sleep(15)
        for repo in sortedRepos:
            repo["index"] = index
            index += 1

        fileClass.writeToFile(
            str(self.language) + "Repos.txt",
            sampling.repoJsons(
                reposList["total_count"],
                reposList["incomplete_results"],
                reposList["status_code"],
                sortedRepos,
            ),
        )
        print("sorted")

    def categorizeAsyncRepos(self):
        print("Started categorize repos to callback, promise, async.")

        tokens = [constants.TOKEN, constants.TOKEN1, constants.TOKEN2, constants.TOKEN3, constants.TOKEN4]
        current_token = 0
        timeOut = 0

        promiseCounter = 0
        callbackCounter = 0
        asyncCounter = 0
        uncategorizedCounter = 0

        promiseRepos = []
        callbackRepos = []
        asyncRepos = []
        uncategorizedRepos = []

        reposList = fileClass.openFile(str(self.language) + "Repos.txt")
        async_keywords = ["callback", "promise", "async"]

        for repo in reposList["repositories"]:
            print("Index: ", repo["index"])
            repoName = repo["repoFullName"]
            print("RepoName: ", repoName)

            timeOut += 1

            if sampling.timeOut(timeOut, 5):
                fileClass.writeToFile(
                    "PromiseRepos.txt",
                    sampling.repoJsons(
                        promiseCounter,
                        reposList["incomplete_results"],
                        reposList["status_code"],
                        promiseRepos,
                    ),
                )
                fileClass.writeToFile(
                    "CallbackRepos.txt",
                    sampling.repoJsons(
                        callbackCounter,
                        reposList["incomplete_results"],
                        reposList["status_code"],
                        callbackRepos,
                    ),
                )
                fileClass.writeToFile(
                    "AsyncRepos.txt",
                    sampling.repoJsons(
                        asyncCounter,
                        reposList["incomplete_results"],
                        reposList["status_code"],
                        asyncRepos,
                    ),
                )
                fileClass.writeToFile(
                    "UncategorizedRepos.txt",
                    sampling.repoJsons(
                        uncategorizedCounter,
                        reposList["incomplete_results"],
                        reposList["status_code"],
                        uncategorizedRepos,
                    ),
                )

            async_count = {key: 0 for key in async_keywords}
            total_files = 0
            for keyword in async_keywords:
                url = f"https://api.github.com/search/code?q={keyword}+in:file+language:JavaScript+repo:{repoName}"
                response = requests.get(url, auth=("gmz-19", tokens[current_token]))
                data = response.json()
                async_count[keyword] = data["total_count"]
                print("Async Count: " + keyword, async_count[keyword])
                total_files += data["total_count"]

            if total_files == 0:
                continue
            if response.status_code == 403:
                # Switch to the next token
                print("Next Token will be used.")
                current_token += 1
                if current_token == len(tokens):
                    current_token = 0
            async_percentage = {key: async_count[key] / total_files for key in async_keywords}
            print(async_percentage)
            files_count_json = {key: async_count[key] for key in async_keywords}
            print("Files Count JSON", files_count_json)
            max_keyword = max(async_percentage, key=async_percentage.get)
            print("Max Keyword", max_keyword)
            max_value = async_percentage[max_keyword]
            print("MAX VALUE", max_value)

            if max_value >= 0.5:
                if max_keyword == "promise":
                    promiseCounter += 1
                    promiseRepos.append(
                        sampling.repoKey(
                            repo["index"],
                            repoName,
                            repo["creationDate"],
                            repo["languages"],
                            repo["stars"],
                            None,
                            None,
                            files_count_json,
                        )
                    )
                    print(promiseRepos)
                elif max_keyword == "callback":
                    callbackCounter += 1
                    callbackRepos.append(
                        sampling.repoKey(
                            repo["index"],
                            repoName,
                            repo["creationDate"],
                            repo["languages"],
                            repo["stars"],
                            None,
                            None,
                            files_count_json,
                        )
                    )
                elif max_keyword in ["async"]:
                    asyncCounter += 1
                    asyncRepos.append(
                        sampling.repoKey(
                            repo["index"],
                            repoName,
                            repo["creationDate"],
                            repo["languages"],
                            repo["stars"],
                            None,
                            None,
                            files_count_json,
                        )
                    )
            else:
                uncategorizedCounter += 1
                uncategorizedRepos.append(
                    sampling.repoKey(
                        repo["index"],
                        repoName,
                        repo["creationDate"],
                        repo["languages"],
                        repo["stars"],
                        None,
                        None,
                        files_count_json,
                    )
                )
        print("categorized")


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
            json.dump(repoJson, file, ensure_ascii=False, indent=4)

    def deleteFiles(self, files):
        """Remove file from os.

        :param files: (list): List of paths to be deleted.
        """
        for file in files:
            os.remove(file)


language = "JavaScript"

fileClass = File()

sampling = Sampling("JavaScript")

sampling.categorizeAsyncRepos()
