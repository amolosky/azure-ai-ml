import re
import subprocess
import sys
from urllib import parse
import runpy
import logging
from contextlib import contextmanager


INVOKER_VERSION = '0.0.8'


def log_dataset_session_id():
    # Try printing the session id for better debugging Dataset issues.
    try:
        from azureml._base_sdk_common import _ClientSessionId
        print('Session_id = ' + _ClientSessionId)
    except Exception:
        print('Session_id cannot be imported.')


@contextmanager
def run_without_logging_config():
    """Execute codes without current configuration of logging.
    Then recover the logging configuration after execution.
    """
    # Remove all current handlers in root logger to make sure logging.basicConfig could work.
    original_handlers = logging.root.handlers
    logging.root.handlers = []
    try:
        # User codes will be executed here.
        yield
    finally:
        # Recover original configuration.
        logging.root.handlers = original_handlers


def run_with_runpy(command):
    with run_without_logging_config():
        module = command[2]
        print(f"Using runpy to invoke module '{module}'.\n")
        # Update sys.argv to make sure the module get correct commands.
        # Before: python -m xxx.xxx --arg1 val1 --arg2 val2
        # After: xxx.xxx --arg1 val1 --arg2 val2
        sys.argv = command[2:]
        runpy.run_module(module, init_globals=globals(), run_name='__main__')
        return 0


def run(command: list, timeout=60000):
    if not command:
        return

    # For the modules using python -m to run, we use runpy to run to avoid subprocess overhead.
    if command[:2] == ['python', '-m']:
        return run_with_runpy(command)

    return subprocess.Popen(command, stdout=sys.stdout, stderr=sys.stderr).wait(timeout=timeout)


def is_invoking_official_module(args):
    return len(args) >= 3 and args[0] == 'python' and args[1] == '-m' and args[2].startswith('azureml.studio.')


def execute(args):
    is_custom_module = not is_invoking_official_module(args)
    module_type = 'custom module' if is_custom_module else 'official module'
    print('Module type: {}.'.format(module_type))
    print('')

    ret = run(args)

    # set the subprocess run result as exit value
    exit(ret)


COMMAND_OPTION_PATTERN = re.compile(r"^--(\w|-)+=.+", re.DOTALL | re.UNICODE)
EXTRA_DOUBLE_QUOTE_PATTERN = re.compile(r"^\"(.*\s.*?)(\\*)\"$", re.DOTALL | re.UNICODE)


# Reverse the escape operation in link below
# https://stackoverflow.com/questions/5510343/escape-command-line-arguments-in-c-sharp/12364234#12364234
def unescape_arg_value(value: str):
    if re.match(EXTRA_DOUBLE_QUOTE_PATTERN, value):
        # Remove double quote in begin and end
        unquoted_value = value[1:-1]
        extra_end_backslash_count = (len(unquoted_value) - len(unquoted_value.rstrip('\\'))) // 2
        value = unquoted_value[:-extra_end_backslash_count] if extra_end_backslash_count > 0 else unquoted_value

    char_array = []
    backslash_seq_count = 0
    for ch in value:
        if ch == '\\':
            backslash_seq_count += 1
        else:
            backslash_seq_count = backslash_seq_count // 2 if ch == '"' else backslash_seq_count
            char_array.extend(backslash_seq_count * ['\\'])
            char_array.append(ch)
            backslash_seq_count = 0

    if backslash_seq_count > 0:
        char_array.extend(backslash_seq_count * ['\\'])

    return ''.join(char_array)


def unescape_arg(arg):
    # If it matches the --<key>=<value> pattern, and the value isn't empty
    # Take the shlex.quote action to the value part only
    if re.search(COMMAND_OPTION_PATTERN, arg):
        # Split by the first '='
        parts = arg.split("=", 1)
        return '{}={}'.format(parts[0], unescape_arg_value(parts[1]))
    return arg


def decode(args):
    return [unescape_arg(parse.unquote_plus(arg)) for arg in args]


if __name__ == '__main__':
    log_dataset_session_id()

    args = sys.argv[1:]
    print(f"Invoking module by urldecode_invoker {INVOKER_VERSION}.")
    print("")

    decoded_args = decode(args)

    execute(decoded_args)
