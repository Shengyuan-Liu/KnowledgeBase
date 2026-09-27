# Raw evidence formatting exception

The staged whitespace check reported ten lines in five actual SDK context files.
The same findings and exit code 2 are retained in [raw-format-1.log](raw-format-1.log)
and its complete [command record](raw-format-1.json). These lines contain original
tab delimiters for empty table cells and trailing empty header positions. Removing
them would alter the canonical evidence under review; the raw text is unchanged.

The appropriately scoped [source-format check](source-format-1.json) passes for
product code, tests, documentation and evaluation scripts. This note was reviewed
for English prose, correct local links and the distinction between immutable raw
evidence and editable source. It changes no code, measurements or acceptance claim.
