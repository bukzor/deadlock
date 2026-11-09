from .dlls_md import escape


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
