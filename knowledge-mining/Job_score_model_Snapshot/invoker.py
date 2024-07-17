import subprocess
import sys
import runpy
import logging
from contextlib import contextmanager


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


INVOKER_VERSION = '0.0.8'


def is_invoking_official_module(args):
    return len(args) >= 3 and args[0] == 'python' and args[1] == '-m' and args[2].startswith('azureml.studio.')


def generate_run_command(args):
    return [arg for arg in args]


def execute(args):
    is_custom_module = not is_invoking_official_module(args)
    module_type = 'custom module' if is_custom_module else 'official module'
    print('Invoking {} by invoker {}.'.format(module_type, INVOKER_VERSION))

    ret = run(generate_run_command(args))

    # set the subprocess run result as exit value
    exit(ret)


if __name__ == '__main__':
    log_dataset_session_id()

    args = sys.argv[1:]
    execute(args)
