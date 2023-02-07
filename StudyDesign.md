# Study Design

###### BSc Thesis: "How Are Different Asynchronous Programming Constructs in JavaScript Related to Software Quality? A Repository Mining Study on GitHub"

##### Research Design
This research conducts a mining software repository (MSR) study. The source of open-source repositories is GitHub, a network-based version management service for software development projects. The selected language for this study is JavaScript, as the title of this thesis suggests. The GitHub REST API is used to obtain the data from the JavaScript repositories.

## Research Questions

### RQ: "How are different asynchronous programming constructs related to software quality?"

#### RQ1: "Does using “callbacks” lead to less functional correctness or maintainability?"
#### RQ2: "Does using “async/await” lead to less functional correctness or maintainability?"
#### RQ2: "Does using “promises” shows better functional correctness or maintainability?"

## Sampling Procedures
Automating the sampling a Python script is created. Using Python’s request library, the data is automatically obtained via the GitHub API. The GitHub Search API is used to set repository requirements, sampling constraints, and to filter asynchronous programming constructs.

### 1. Repository requirements
In order to obtain only relevant repositories, certain requirements must apply. For this study, repositories from the last ten years are analyzed, which corresponds to the date range from the beginning of January 2013 to the beginning of January 2023. Since applications always contain content of other languages or additional backends, the percentage value of the primary language, for this study JavaScript, is 60%. Considering only repositories with activity, repositories with more than 5 stars are selected and those that were last modified in the last three months at least once. Furthermore, the repositories are not allowed to be a fork, i.e., a copy, but if the repository has many forks, it shows in popularity. Since JavaScript repositories developed with the Vue.js framework are labeled as own programming language ["Vue" in GitHub](https://github.com/search?q=language%3Avue&type=repositories), these repositories are also additionally filtered.

### 2. Filter asynchronous JavaScrip repositories
To filter asynchronous code from all JavaScript repositories, the GitHub Search API is used, which enables requests to repositories, code, commits, issues, topics, wikis, etc. With [topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics), it is possible to explore repositories in a particular subject area, find projects to contribute to, and discover new solutions to a specific problem. With appropriate asynchronous-related keywords, it is possible to find candidate asynchronous repositories. Since the GitHub API has a [limitation on query length](https://docs.github.com/en/rest/search?apiVersion=2022-11-28#limitations-on-query-length), which goes along with a limitation of a maximum of five AND, OR or NOT operators, a maximum of six keywords can be used for the query: "callback", "async", "await", "promise", "fetch" and "ajax".

### 3. Categorize collected repositories


### 4. Filter repositories with cloed bug issues and bug fix commits
Only repositories with more than 20 commits are taken into consideration to ensure sufficient development activity, such as to prevent dead projects or projects where all code was pushed within a few commits. To collect asynchronous bugs, repositories must have closed bug issues and bug fix commits that are in English.


## Data Collection Procedures

Similar to the Sampling Procedures, a Python script is used to automatically collect the necessary data from the chosen projects. The GitHub API and the static analysis tool [SonarQube](https://next.sonarqube.com/sonarqube/web_api/) with its API served as the two main data sources. All repositories are downloaded using the GitHub API because SonarQube requires the source code for analysis.

### Software Quality Metrics

#### [Functional Correctness](https://iso25000.com/index.php/en/iso-25000-standards/iso-25010)
Degree to which a product or system provides the correct results with the needed degree of precision.
The unit of measure of functional correctness is defect density, the number of defects per line of code. In a given piece of software, the defect density ought to approach zero over time. It is possible to estimate the defect density of undiscovered bugs in a piece of software by tracking the number of bugs over time.

##### Bug resolution time
Average Time a Bug Issue is Open.

##### Bug fix commit ratio
Percentage of Bug-Fix Commits.

#### [Maintainability](https://iso25000.com/index.php/en/iso-25000-standards/iso-25010/57-maintainability)
This characteristic represents the degree of effectiveness and efficiency with which a product or system can be modified to improve it, correct it or adapt it to changes in environment, and in requirements.

##### Code smells per LoC

##### Cognitive Complexity per LoC

## Hypotheses

#### For RQ1

- [ ] Null Hypotheses:
- [ ] Alternative Hyperthesis:

##### For RQ2

- [ ] Null Hypotheses:
- [ ] Alternative Hyperthesis:

##### For RQ3

- [ ] Null Hypotheses:
- [ ] Alternative Hyperthesis:  

## Analysis Procedures

- [ ] Which tools for analysis
- [ ] Benchmark of tools which to use
- [ ] Advantages and Disadvantages of a tool and their measuring metrics

## Validty Procedures

- [ ] ?
