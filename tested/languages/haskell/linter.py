import json
import logging
from pathlib import Path
from typing import Tuple, List

from tested.configs import Bundle
from tested.dodona import AnnotateCode, Message, ExtendedMessage, Permission, \
    Severity
from tested.internationalization import get_i18n_string
from tested.judge.utils import run_command

logger = logging.getLogger(__name__)

message_categories = {
    'Error':      Severity.ERROR,
    'Warning':    Severity.WARNING,
    'Suggestion': Severity.INFO
}


def run_hlint(bundle: Bundle, submission: Path, remaining: float) \
        -> Tuple[List[Message], List[AnnotateCode]]:
    """
    Calls eslint to annotate submitted source code and adds resulting score and
    annotations to tab.
    """
    config = bundle.config
    language_options = bundle.config.config_for()
    if language_options.get("hlint_config", None):
        config_path = config.resources / language_options.get('hlint_config')
    else:
        # Use the default file.
        config_path = config.judge / "tested/languages/haskell/hlint.yml"
    config_path = config_path.absolute()

    execution_results = run_command(
        directory=submission.parent,
        timeout=remaining,
        command=["hlint", "-j", "--json", "-h", config_path,
                 submission.absolute()]
    )

    if execution_results is None:
        return [], []

    if execution_results.timeout or execution_results.memory:
        return [get_i18n_string(
            "languages.haskell.linter.timeout") if execution_results.timeout else
                get_i18n_string("languages.haskell.linter.memory")], []

    try:
        hlint_messages = json.loads(execution_results.stdout)
    except Exception as e:
        logger.warning("HLint produced bad output", exc_info=e)
        return [get_i18n_string("languages.haskell.linter.output"),
                ExtendedMessage(
                    description=str(e),
                    format='code',
                    permission=Permission.STAFF
                )], []
    annotations = []

    for hlint_message in hlint_messages:
        if Path(hlint_message['file']).name != submission.name:
            continue
        notes = '\n'.join(hlint_message['note'])
        annotations.append(AnnotateCode(
            row=max(int(hlint_message['startLine']) - 1, 0),
            text=f"{hlint_message['hint']}\nfrom: `{hlint_message['from']}`\n"
                 f"to: `{hlint_message['to']}`\n{notes}",
            column=max(int(hlint_message['startColumn']) - 1, 0),
            type=message_categories.get(hlint_message['severity'],
                                        Severity.WARNING),
        ))
    # sort linting messages on line, column and code
    annotations.sort(key=lambda a: (a.row, a.column, a.text))
    return [], annotations
