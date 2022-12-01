# Token from GitHub
TOKEN = ""

# Token from GitHub
TOKEN1 = ""

# Token from GitHub
TOKEN2 = ""

# Token from GitHub
TOKEN4 = ""

# Token from GitHub
TOKEN5 = ""

# Token from GitHub
TOKEN6 = ""

# Token from SonarQube
TOKEN3 = ""

REPOSCHARACTERISTICS = [
    "index",
    "repo_name",
    "ncloc",
    "code_smells",
    "any-type_count",
    "cognitive_complexity",
    "framework",
    "bug_issues_count",
    "bug-fix_commits_count",
    "commits_count",
]

METRICS = [
    "index",
    "repo_name",
    "code-smells_ncloc",
    "bug-fix-commits_ratio",
    "avg_bug-issue_time",
    "cognitive-complexity_ncloc",
]

CALCULATEDVALS = ["", "react", "angular", "vue", "others"]

ESLINTFILES = ["./eslint/.eslintignore", "./eslint/.eslintrc.js"]

URLCREATEPROJECT = "http://localhost:9000/api/projects/create"
URLGENERATETOKEN = "http://localhost:9000/api/user_tokens/generate"
URLISSUES = "http://localhost:9000/api/issues/search"
URLCOMPONENTREE = "http://localhost:9000/api/measures/component_tree"

ESLINTPATHS = [
    ".eslintrc",
    ".eslintrc.json",
    ".eslintrc.js",
    ".eslintignore",
    ".eslintrc.yml",
    ".eslintrc.yaml",
]
