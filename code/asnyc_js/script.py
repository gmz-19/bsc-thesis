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
    """In this class, individual methods are implemented that were executed for sampling. The sampling process is iterative and cannot be performed in one single step. More about this can be found in the paper."""

    def __init__(self, language):
        """Set date here.
        Args:
            language (string): The programming language for which the functions from this class should be executed.
        """
        self.language = language
        self.startDate = dt.date(2013, 12, 24)
        self.endDate = dt.date(2023, 1, 1)
        self.incompleteResult = False
        self.errorCode = "200"
        self.counter = 0
        self.counter2 = 0
        pass

    def requestRepos(self):
        """This is the first step of sampling. In this function, all repos that match the characteristics are stored in a file. More to the characteristics at the request url."""

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

    def checkApiLimit(self, username):
        """Check how many requests have already been made this hour. Change token number in function.

        Args:
            username (string): The username behind the token.
        """
        url = f"https://api.github.com/users/{username}"
        test = requests.head(url, auth=("username", constants.TOKEN3))
        # print(test.headers)
        # print("Rate Limit:", test.headers.get("X-RateLimit-Limit'"))
        print(test.headers.get("X-Ratelimit-Remaining"))
        # print("Resets in:", test.headers.get("X-Ratelimit-Reset"))"""

    def sortReposByStars(self):
        """Sorts the repo list by stars and gives each repo an id."""
        print("started")
        reposList = fileClass.openFile(str(self.language) + "Repos.txt")
        repos = reposList["repositories"]

        sortedRepos = sorted(repos, key=lambda repo: repo["stars"], reverse=True)

        index = 1
        time.sleep(15)
        for repo in repos:
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

    def setErrorToDefault(self):
        self.incompleteResult = False
        self.errorCode = "200"

    def daterange(self, startDate, endDate):
        """Function that gives the range of the date.

        Args:
            startDate (date): Date of the first repo to be examined.
            endDate (date): Date of the last repo to be examined.

        Yields:
            list: List of all dates in the given range.
        """
        for n in range(int((endDate - startDate).days)):
            yield startDate + timedelta(n)

    def timeOut(self, currRequestCount, timeOutRequestNumb):
        """If more than the allowed number of requests is exceeded, there will be a one-minute pause.
        Args:
            currRequestCount ([integer): Cur number of request.
            timeOutRequestNumb (integer): If this number is exceeded, a timeout is made.

        Returns:
            boolean: If a timeout is necessary
        """
        if currRequestCount % timeOutRequestNumb == 0:
            self.counter = 0
            time.sleep(60)
            return True

    def repoKey(
            self, index, repoFullName, creationDate, languages, stars, issues, commits
    ):
        return {
            "index": index,
            "repoFullName": repoFullName,
            "creationDate": creationDate,
            "languages": languages,
            "stars": stars,
            "issues": issues,
            "commits": commits,
        }

    def requestLanguages(self, repoName):
        """Function to get all languages used in the repo.

        Args:
            repoName (boolean): The complete name of a GitHub repository.

        Returns:
            json: Json of the languages used in the repo.
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


class File:
    """All functions related to the json file are in this class."""

    def __init__(self):
        pass

    def openFile(self, fileName):
        """Opens txt file.

        Args:
            fileName (string): Complete filename with pl.

        Returns:
            list: Json of the txt file.
        """
        try:
            with open(fileName, encoding="utf8") as f:
                return json.load(f)
        except:
            print("Create default file")
            fileClass.writeToFile(fileName, None)

    def writeToFile(self, fileName, repoJson):
        """Writes to txt file.

        Args:
            fileName (string): Complete filename with pl.
            repoJson (list): The json object to written in the txt file.
        """
        with open(fileName, "w", encoding="utf-8") as file:
            json.dump(repoJson, file, ensure_ascii=False, indent=4)

    def deleteFiles(self, files):
        """Remove file from os.

        Args:
            files (list): List of paths to be deleted.
        """
        for file in files:
            os.remove(file)


language = "JavaScript"

fileClass = File()

sampling = Sampling("JavaScript")

sampling.requestRepos()
