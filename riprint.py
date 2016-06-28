import sys

HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

def pr_newline(bcolor, msg):
    print("%s%s%s" % (bcolor, msg, ENDC))

def pr_sameline(bcolor, msg):
    sys.stdout.write("%s\r" % (msg))
    sys.stdout.flush()

def pr_custom(bcolor, sameline=False):
    return lambda msg: pr_sameline(bcolor, msg) if sameline else pr_newline(bcolor, msg)

def pr_header(msg, sameline=False):
    pr_custom(HEADER, sameline)(msg)

def pr_okblue(msg, sameline=False):
    pr_custom(OKBLUE, sameline)(msg)

def pr_okgreen(msg, sameline=False):
    pr_custom(OKGREEN, sameline)(msg)

def pr_warning(msg, sameline=False):
    pr_custom(WARNING, sameline)(msg)

def pr_fail(msg, sameline=False):
    pr_custom(FAIL, sameline)(msg)

def pr_bold(msg, sameline=False):
    pr_custom(BOLD, sameline)(msg)

def pr_underline(msg, sameline=False):
    pr_custom(UNDERLINE, sameline)(msg)


