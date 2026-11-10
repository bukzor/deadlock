from .dlls_convars_md import page

TSV = """\
dll	name	type	version	default	min	max	flags	help
client.dll	sv_slack	float32	0	0.026	0.0	1.0	replicated cheat	Slack <mult>.\\n
client.dll	citadel_tab	int32	3	-1	\\N	\\N	archive	\\N
client.dll	fog_color	vector3	0	-1.0 -1.0 -1.0	\\N	\\N		\\N
server.dll	sv_name	string	0		\\N	\\N		\\N
server.dll	sv_ref	bool	0	\\N	\\N	12		\\N
"""


class DescribePage:
    def it_lists_each_convar_with_its_type_default_range_version_flags_and_help(self):
        assert page(TSV) == """\
# Console variables

5 declarations in 2 DLLs, from `data/dlls/convars.tsv`.

- [client.dll](#clientdll) (3)
- [server.dll](#serverdll) (2)

## client.dll

- `citadel_tab` · int32 = `-1` · version 3 · *archive*
- `fog_color` · vector3 = `-1.0 -1.0 -1.0`
- `sv_slack` · float32 = `0.026` · min `0.0` · max `1.0` · *replicated cheat*\\
  Slack \\<mult\\>.

## server.dll

- `sv_name` · string = *empty*
- `sv_ref` · bool · max `12`
"""
