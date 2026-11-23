from .dlls_concommands_md import page

TSV = """\
dll	name	flags	help
client.dll	zz_last	release	Opens <MatchID>.\\n\\tArguments: [salt]
client.dll	aa_first	cheat developmentonly	\\N
client.dll	aa_first		second\\n\\n  declaration 
server.dll	kill	release\t
"""


class DescribePage:
    def it_lists_each_dlls_commands_by_name_with_flags_and_help(self):
        assert page(TSV) == """\
# Console commands

4 declarations in 2 DLLs, from `data/dlls/concommands.tsv`.

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
