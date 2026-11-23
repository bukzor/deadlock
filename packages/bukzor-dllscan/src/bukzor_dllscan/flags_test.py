import pytest

from .flags import BY_BIT, names


class DescribeByBit:
    def it_covers_every_s2sdk_bit(self):
        assert sorted(BY_BIT) == [*range(31), 32, 33, 34, 36, 37]

    def it_spells_names_as_dumpsource2_does(self):
        assert BY_BIT[22] == "notconnected"
        assert BY_BIT[37] == "enum_value"


class DescribeNames:
    def it_names_no_flags_as_nothing(self):
        assert names(0) == ()

    def it_names_one_bit(self):
        assert names(1 << 14) == ("cheat",)

    def it_lists_a_multi_bit_word_in_bit_order(self):
        word = 1 << 14 | 1 << 13 | 1 << 1 | 1 << 0
        assert names(word) == (
            "linked_concommand",
            "developmentonly",
            "replicated",
            "cheat",
        )

    def it_names_an_unknown_bit_by_its_index(self):
        assert names(1 << 38) == ("flag_38",)

    def it_puts_unknown_bits_after_named_ones(self):
        assert names(1 << 35 | 1 << 32 | 1 << 31 | 1 << 2) == (
            "gamedll",
            "defensive",
            "flag_31",
            "flag_35",
        )

    @pytest.mark.parametrize("word", [-1, 1 << 64])
    def it_rejects_a_word_outside_64_bits(self, word: int):
        with pytest.raises(AssertionError):
            _ = names(word)
