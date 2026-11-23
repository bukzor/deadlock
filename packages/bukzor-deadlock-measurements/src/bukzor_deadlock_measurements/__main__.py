import sys

from .load import load_all
from .summary import format_table

_ = sys.stdout.write(format_table(load_all()))
