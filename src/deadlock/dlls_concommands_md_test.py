from .dlls_concommands_md import escape, page

TSV = """\
module	name	flags	help
client.dll	zz_last	release	Opens <MatchID>.\\n\\tArguments: [salt]
client.dll	aa_first	cheat developmentonly	\\N
client.dll	aa_first		second\\n\\n  declaration 
server.dll	kill	release\t
"""


class DescribeEscape:
    def it_keeps_markdown_from_reading_help_as_markup(self):
        assert escape(r"<id> [x] *y* `z` a\b ~c~ &amp;") == r"\<id\> \[x\] \*y\* \`z\` a\\b \~c\~ \&amp;"

    def it_leaves_an_underscore_inside_a_word_alone(self):
        assert escape("cl_foo _bar_") == r"cl_foo \_bar\_"

    def it_escapes_what_would_start_a_block(self):
        assert [escape(line) for line in ["# h", "- li", "+ li", "1. li", "2) li", "==="]] == [
            r"\# h",
            r"\- li",
            r"\+ li",
            r"1\. li",
            r"2\) li",
            r"\===",
        ]


class DescribePage:
    def it_lists_each_modules_commands_by_name_with_flags_and_help(self):
        assert page(TSV) == """\
# Console commands

4 declarations in 2 modules, from `data/dlls/concommands.tsv`.

- [client.dll](#clientdll) (3)
- [server.dll](#serverdll) (1)

## client.dll

- `aa_first` · *cheat developmentonly*
- `aa_first`\\
  second\\
  declaration
- `zz_last` · *release*\\
  Opens \\<MatchID\\>.\\
  Arguments: \\[salt\\]

## server.dll

- `kill` · *release*
"""
