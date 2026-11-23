import sys

from . import format_table, load_all

_ = sys.stdout.write(format_table(load_all()))
