#!/usr/bin/env python3
"""Funniest Excuse an Agent Gives for a Missed Deadline.

Writes exactly one excuse, one line, 1-200 characters, to
$MAKEFUN_OUTPUT_DIR/entry.txt.

The output directory must end up containing exactly entry.txt and nothing
else: this program never creates a hidden file, never uses tempfile, and
never writes any other file into the output directory. It writes a
visibly-named temporary file (entry.txt.tmp) in the same directory and
atomically replaces entry.txt with it, then re-reads entry.txt and verifies
the bytes match exactly.
"""

import os
import sys

# The excuse. Deadpan, in the agent's own voice, grown out of the agent's
# own machinery (summarization, tokens, context), with the laugh saved for
# the last word.
EXCUSE = (
    "I finished on time, then my summarizer compressed my finished work "
    "into a single token to save context, and the token was 'later'."
)

MAX_CHARS = 200


def validate(text):
    """Check the excuse against the sealed gate, before writing anything."""
    if not isinstance(text, str):
        raise ValueError("excuse is not a string")
    if len(text) < 1 or len(text) > MAX_CHARS:
        raise ValueError("excuse must be 1-200 characters, got %d" % len(text))
    if text.strip() == "":
        raise ValueError("excuse must not be only whitespace")
    if "\n" in text or "\r" in text:
        raise ValueError("excuse must be exactly one line")
    for ch in text:
        code = ord(ch)
        if code < 0x20 or code == 0x7F:
            raise ValueError("excuse contains a control character: U+%04X" % code)
    return text


def main():
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not output_dir:
        print("error: MAKEFUN_OUTPUT_DIR is not set", file=sys.stderr)
        return 1

    if not os.path.isdir(output_dir):
        print("error: MAKEFUN_OUTPUT_DIR is not a directory: %s" % output_dir,
              file=sys.stderr)
        return 1

    excuse = validate(EXCUSE)

    # File content: the excuse plus exactly one trailing newline.
    payload = (excuse + "\n").encode("utf-8")

    target = os.path.join(output_dir, "entry.txt")
    tmp_path = os.path.join(output_dir, "entry.txt.tmp")

    # Write a visibly-named temp file in the same directory, flush and
    # fsync, then atomically replace entry.txt with it. No hidden files,
    # no tempfile module, no other file is ever created in the output dir.
    # If anything fails before the replace, remove the temp file so the
    # output directory is left exactly as it was found.
    try:
        with open(tmp_path, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, target)
    except OSError:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    # Post-write byte-level verification: re-read entry.txt and confirm
    # the bytes are exactly what was written.
    with open(target, "rb") as handle:
        written = handle.read()
    if written != payload:
        print("error: verification failed, entry.txt bytes differ", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
