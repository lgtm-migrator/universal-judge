import logging
import os
import stat
from multiprocessing.dummy import Pool
from pathlib import Path
from typing import Tuple

from dodona import *
from dodona import report_update, StartJudgment, StartTab, StartContext, CloseContext, CloseTab, CloseJudgment
from evaluators import get_evaluator, Evaluator
from runners.runner import Runner, ExecutionResult, get_generator, BaseExecutionResult, get_supporting_languages, \
    ContextExecution
from tested import Config
from testplan import *

logger = logging.getLogger(__name__)


def _evaluate_channel(
        out: IO,
        channel_name: str,
        expected_output: Union[OutputChannel, AnyChannelState],
        actual_result: Optional[str],
        evaluator: Evaluator) -> bool:
    """
    Evaluate the output on a given channel. This function will output the appropriate messages
    to start and end a new test in Dodona.

    If errors is given, the test will end with a runtime error. Note that if the expected output
    is None, the test will not be written to Dodona if everything is correct.

    :param out: The output file for the judge.
    :param channel_name: The name of the channel being evaluated. Will be displayed in Dodona.
    :param expected_output: The output channel from the test case.
    :param actual_result: The actual output. Can be None, depending on the evaluator.
    :param evaluator: The evaluator to use.
    :return: True if successful, otherwise False.
    """
    evaluation_result = evaluator.evaluate(expected_output, actual_result)
    status = evaluation_result.result

    # If the actual value is empty and the expected output is None or ignored, don't report it.
    is_correct = status.enum == Status.CORRECT
    has_no_result = actual_result is None or actual_result == ""
    has_no_expected = expected_output == NoneChannelState.NONE or expected_output == IgnoredChannelState.IGNORED
    if is_correct and has_no_result and has_no_expected:
        return True

    report_update(out, StartTest(expected=evaluation_result.readable_expected))

    # Report any messages we received.
    for message in evaluation_result.messages:
        report_update(out, AppendMessage(message=message))

    # Close the test.
    report_update(out, CloseTest(generated=evaluation_result.readable_actual,
                                 status=status,
                                 data=TestData(channel=channel_name)))

    return is_correct


def _check_features(plan: Plan, language: str):
    """
    Check if a language supports all features needed by a certain testplan.
    In the future, we might also want to determine which languages support all required features,
    but that is currently not needed.
    :param plan:
    :param language: The programming language.
    """
    supported = get_supporting_languages(plan)
    if language not in supported:
        raise TestPlanError(f"The chosen language {language} does not support all required features for the testplan.")


@dataclass
class MetaContext:
    """Contains a context and some metadata about the context."""
    tab_index: int  # The index of the tab this context belongs to.
    context_index: int  # The index of this context in its tab.
    context: Context  # The actual context.


class GeneratorJudge:
    runner: Runner

    def __init__(self, config: Config, output: IO):
        self.config = config
        self.out = output
        self.runner = get_generator(config)

    def _process_compile_results(self, results: Optional[BaseExecutionResult]) -> Tuple[List[Message], Status]:
        """Process compilation output. This is called inside a context."""

        messages = []

        # There was no compilation
        if results is None:
            return messages, Status.CORRECT

        # Report stdout.
        if results.stdout:
            # Append compiler messages to the output.
            messages.append("De compiler produceerde volgende uitvoer op stdout:")
            messages.append(ExtendedMessage(description=results.stdout, format='code'))

        # Report stderr.
        if results.stderr:
            # Append compiler messages to the output.
            messages.append("De compiler produceerde volgende uitvoer op stderr:")
            messages.append(ExtendedMessage(description=results.stderr, format='code'))

        # Report errors if needed.
        if results.exit != 0:
            messages.append(f"Het compilatieproces eindigde met exitcode {results.exit}")
            return messages, Status.COMPILATION_ERROR
        else:
            return messages, Status.CORRECT

    def _process_results(self,
                         context: Context,
                         results: ExecutionResult,
                         compiler_results: Tuple[List[Message], Status]):
        # Process output
        stdout_ = results.stdout.split(results.separator) if results is not None else []
        stderr_ = results.stderr.split(results.separator) if results is not None else []
        values = results.results.split(results.separator) if results is not None else []
        exceptions = results.exceptions.split(results.separator) if results is not None else []

        # There might be less output than testcase, which is an error. However, we process the
        # output we have, to ensure we send as much feedback as possible to the user.
        testcase: Testcase  # Type hint for pycharm.
        for i, testcase in enumerate(context.all_testcases()):

            readable_input = self.runner.get_readable_input(testcase)
            report_update(self.out, StartTestcase(description=readable_input))

            # Handle compiler results
            if compiler_results[1] != Status.CORRECT:
                for message in compiler_results[0]:
                    report_update(self.out, AppendMessage(message=message))
                report_update(self.out, EscalateStatus(status=StatusMessage(enum=compiler_results[1])))
                report_update(self.out, CloseTestcase(accepted=False))
                break
            else:
                assert results is not None

            # Get the evaluators
            try:
                stdout_evaluator = get_evaluator(self.config, testcase.output.stdout)
                stderr_evaluator = get_evaluator(self.config, testcase.output.stderr)
                file_evaluator = get_evaluator(self.config, testcase.output.file)
                value_evaluator = get_evaluator(self.config, testcase.output.result)
                exception_evaluator = get_evaluator(self.config, testcase.output.exception)
            except TestPlanError as e:
                report_update(self.out, AppendMessage(message=ExtendedMessage(
                    description=str(e),
                    format='text',
                    permission=Permission.STAFF
                )))
                break

            # Evaluate the file channel.
            results = [_evaluate_channel(self.out, "file", testcase.output.file, None, file_evaluator)]

            # Evaluate the stderr channel
            actual_stderr = stderr_[i] if i < len(stderr_) else None
            results.append(_evaluate_channel(
                self.out, "stderr", testcase.output.stderr, actual_stderr, stderr_evaluator
            ))

            actual_exception = exceptions[i] if i < len(exceptions) else None
            results.append(_evaluate_channel(
                self.out, "exception", testcase.output.exception, actual_exception, exception_evaluator
            ))

            actual_stdout = stdout_[i] if i < len(stdout_) else None
            results.append(_evaluate_channel(
                self.out, "stdout", testcase.output.stdout, actual_stdout, stdout_evaluator
            ))

            actual_value = values[i] if i < len(values) else None
            results.append(_evaluate_channel(self.out, "return", testcase.output.result, actual_value, value_evaluator))

            # Check if there is early termination.
            if i >= len(stdout_) or i >= len(stderr_) or i >= len(values) or i >= len(exceptions):
                report_update(self.out, AppendMessage(message=ExtendedMessage(
                    description="Tests were terminated early.", format='text'
                )))

            report_update(self.out, CloseTestcase())

            # If this was an essential testcase with an error, stop testing now.
            if testcase.essential and not all(results):
                break

    def judge(self, plan: Plan):
        """Execute the test plan for an exercise, resulting in a judgment."""
        # Check we have the required features.
        logger.info("Checking supported features...")
        _check_features(plan, self.config.programming_language)
        report_update(self.out, StartJudgment())
        common_dir = Path(self.config.workdir, f"common")
        common_dir.mkdir()
        logger.info("Start generating code...")
        result, files = self.runner.generate(plan, common_dir)
        compiler_results = self._process_compile_results(result)
        self._protect_common_dir(common_dir)
        try:
            logger.info("Start judging code...")
            pool = Pool()
            for tab_index, tab in enumerate(plan.tabs):
                report_update(self.out, StartTab(title=tab.name))
                # Create a list of arguments to execute (in threads)
                executions = []
                for context_index, context in enumerate(tab.contexts):
                    # Create a working directory for the context.
                    directory = Path(self.config.workdir, f"context-{tab_index + context_index}")
                    directory.mkdir()
                    executions.append(ContextExecution(
                        plan,
                        context,
                        tab_index + context_index,
                        directory,
                        common_dir,
                        files
                    ))

                # Do the executions in parallel
                results = pool.map(lambda a: self.runner.execute(a), executions)

                # Handle the results
                for context_index, context in enumerate(tab.contexts):
                    report_update(self.out, StartContext(description=context.description))
                    execution_result = results[context_index]
                    self._process_results(context, execution_result, compiler_results)
                    report_update(self.out, CloseContext())
                report_update(self.out, CloseTab())
            report_update(self.out, CloseJudgment())
        finally:
            self._unprotect_common_dir(common_dir)

    def _protect_common_dir(self, directory):
        # Make the common folder read-only, making it more difficult to mess
        # with the code.
        logger.info("Making %s read-only", directory)
        os.chmod(directory, stat.S_IREAD)  # Disable write access

    def _unprotect_common_dir(self, directory):
        logger.info("Giving write-access to %s", directory)
        os.chmod(directory, stat.S_IREAD | stat.S_IWRITE)
