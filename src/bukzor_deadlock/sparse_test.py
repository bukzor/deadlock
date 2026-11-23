from .sparse import Table, join, parse, render, split

DENSE: Table = (
    ["hero", "health", "crouch", "flag"],
    [
        ["hero_a", "700", "4.75", ""],
        ["hero_b", "780", "4.75", ""],
    ],
)


class DescribeSplit:
    def it_moves_every_single_valued_column_to_the_defaults(self):
        sparse, defaults = split(DENSE)
        assert sparse == (["hero", "health"], [["hero_a", "700"], ["hero_b", "780"]])
        assert defaults == {"crouch": "4.75", "flag": ""}

    def it_keeps_the_leading_key_column_even_when_single_valued(self):
        sparse, defaults = split((["hero", "health"], [["hero_a", "700"]]))
        assert sparse == (["hero"], [["hero_a"]])
        assert defaults == {"health": "700"}

    def it_moves_nothing_from_a_table_with_no_rows(self):
        assert split((["hero", "health"], [])) == ((["hero", "health"], []), {})


class DescribeJoin:
    def it_inverts_split(self):
        assert join(*split(DENSE)) == DENSE

    def it_appends_default_columns_after_the_sparse_ones(self):
        sparse: Table = (["hero", "flag"], [["hero_a", "x"], ["hero_b", ""]])
        dense: Table = (["hero", "flag", "crouch"], [["hero_a", "x", "4.75"], ["hero_b", "", "4.75"]])
        assert join(*split(dense)) == dense
        assert join(sparse, {"crouch": "4.75"}) == dense


class DescribeParse:
    def it_inverts_render(self):
        text = "hero\thealth\tflag\nhero_a\t700\t\n"
        assert render(parse(text)) == text

    def it_reads_defaults_as_a_column_value_table(self):
        assert parse("column\tvalue\ncrouch\t4.75\nflag\t\n") == (
            ["column", "value"],
            [["crouch", "4.75"], ["flag", ""]],
        )
