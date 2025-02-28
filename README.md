# TESTed: universal judge for educational software testing

TESTed is a software test framework to evaluate submissions for programming exercises across multiple programming languages, using a single test suite per exercise.

## Installing TESTed

TESTed is implemented in Python, but has various dependencies for its language-specific modules.
We only use the Python language module in this README, but see [dependencies.md](./dependencies.md) for an overview of dependencies for each of the supported programming languages.

Install [Python 3.9](https://www.python.org/downloads/) or later (including pip).
Next, [clone](https://github.com/git-guides/git-clone) the TESTed repository and open a command prompt in the cloned repository.
Now you can run the following commands to install the necessary Python dependencies:

```bash
# Core dependencies
$ pip install -r requirements.txt
# Only needed if you want to run tests
$ pip install -r requirements-tests.txt
# Needed to evaluate submissions in Python
$ pip install -r tested/languages/python/requirements.txt
```

## Running TESTed

TESTed evaluates a submission for a programming exercise based on a test suite that specifies some test cases for the exercise.
In what follows, we guide you through the configuration of a simple programming exercise and running TESTed to evaluate a submission using the test suite of the exercise.
The directory `./exercise/` in the root directory of TESTed contains some more examples of programming exercises with test suites for TESTed.

### 1. Create an exercise

Let's configure a simple programming exercise that asks to implement a function `echo`.
The function takes a single argument and returns its argument.

Start creating a directory for the configuration of the exercise.
To keep things simple, we add the exercise to the `exercise` subdirectory in the root directory of TESTed.

```bash
mkdir exercise/simple-example
```

Note you would normally not store your exercises in the TESTed repository.
We recommend creating a new repository for your exercises.

### 2. Create a test suite

The next step is to design a test suite that will be used to evaluate submission for the exercise.
Again, to keep things simple, we will only include a single test case in the test suite.

```json
{
 "tabs": [
  {
   "name": "Echo",
   "runs": [
    {
     "contexts": [
      {
       "testcases": [
        {
         "input": {
          "type": "function",
          "name": "echo",
          "arguments": [
           {
            "type": "text",
            "data": "input-1"
           }
          ]
         },
         "output": {
          "result": {
           "value": {
            "type": "text",
            "data": "input-1"
           }
          }
         }
        }
       ]
      }
     ]
    }
   ]
  }
 ]
}
```

While being somewhat verbose, the test suite is pretty straightforward.
It contains a single tab "Echo", containing a single run, containing a single context, containing a single test case.
The test case calls the function `echo` with string argument `"input-1"` and sets the string `"input-1"` as the expected return value.
Put the file containing the test suite in the following location:

```bash
# Create the file
$ touch exercise/simple-example/testsuite.json
# Now you should put the content from above in the file.
```

### 3. Create some submissions

Now create two Python submissions for the programming exercise.
The first one contains a correct solution, and the second one returns the wrong result.

```bash
$ cat exercise/simple-example/correct.py
def echo(argument):
  return argument
$ cat exercise/simple-example/wrong.py
def echo(argument):
  # Oops, this is wrong.
  return argument * 2
```

### 4. Evaluate the submissions

To evaluate a submission with TESTed, you need to provide a test suite and configuration information.
This information can be piped to TESTed via stdin, but to make things easier, we will add the information to a configuration file in the directory of the exercise.
In practice, this configuration file could be composed by the learning environment in which TESTed is integrated.

```bash
$ cat exercise/simple-example/config.json
{
  "programming_language": "python",
  "natural_language": "en",
  "resources": "exercise/simple-example/",
  "source": "exercise/simple-example/correct.py",
  "judge": ".",
  "workdir": "workdir/",
  "plan_name": "testsuite.json",
  "memory_limit": 536870912,
  "time_limit": 60
}
```

These attributes are used by TESTed:

- `programming_language`: programming language of the submission
- `resources`: path of a directory with resources TESTed can use
- `source`: path of the submission that must be evaluated
- `judge`: path of the root directory of TESTEd
- `workdir`: path of a temporary directory (see below)
- `plan_name`: path of the test suite, relative to the resources directory (as defined above)

Before evaluating a submission, TESTed generates test code in the workdir.
Create that directory:

```bash
$ mkdir workdir/
```

The content in this directory stays in place after TESTed finishes its evaluation, so you can inspect the generated test code.
Before running TESTed again, you'll need to clear this directory.

With this command, TESTed will evaluate the submission and generate feedback on stdout.

```bash
$ python -m tested -c exercise/simple-example/config.json
{"command": "start-judgement"}
{"title": "Echo", "command": "start-tab"}
{"command": "start-context"}
{"description": {"description": "echo('input-1')", "format": "python"}, "command": "start-testcase"}
{"expected": "input-1", "channel": "return (String)", "command": "start-test"}
{"generated": "input-1", "status": {"enum": "correct"}, "command": "close-test"}
{"command": "close-testcase"}
{"command": "close-context"}
{"command": "close-tab"}
{"command": "close-judgement"}
```
By default, TESTed generates its feedback on stdout. The feedback is formatted in the [JSON Lines](https://jsonlines.org/) text format, meaning that each line contains a JSON object. Here's how you get an overview of all options supported by TESTed:

```bash
$ python -m tested --help
usage: __main__.py [-h] [-c CONFIG] [-o OUTPUT] [-v]

The programming language agnostic educational test framework.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Where to read the config from
  -o OUTPUT, --output OUTPUT
                        Where the judge output should be written to.
  -v, --verbose         Include verbose logs. It is recommended to also use -o in this case.
```

Adjust the configuration file if you want to evaluate the wrong submission.

Here are some more useful features of TESTed:

```bash
# Prints the JSON Schema of the test suite format
$ python -m tested.testplan
# Run a hard-coded exercise with logs enabled, useful for debugging
$ python -m tested.manual
```

## TESTed repository

The repository of TESTed is organized as follows:

- `exercise`: exercises with preconfigured test suites; useful to play around with TESTed and also used by unit tests for TESTed itself
- `tested`: Python code of the actual judge (run by Dodona)
- `tests`: unit tests for TESTed
- `benchmarking`: utilities to benchmark TESTed

You can run the basic unit tests with:

```bash
$ python -m pytest tests/test_functionality.py
```
