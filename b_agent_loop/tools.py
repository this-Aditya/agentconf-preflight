"""
tools.py — two real tools: list_dir and read_file.

Real filesystem, not a dict. Point a loop at this repo and it can genuinely
explore it.

Four design decisions here are worth more than the code, because each one is a
problem you only notice once a model is driving:

1. NEVER RAISE. Every failure returns a readable string. An exception escapes
   through your loop and kills it; a returned string becomes the model's next
   piece of evidence, and it can recover. The wording matters — it is prompt
   text, not a log line.

2. STAY INSIDE THE REPO. Both tools refuse any path that resolves outside ROOT.
   Note "resolves": .resolve() follows symlinks before the check, so a symlink
   pointing out of the repo is refused too. That is why read_file('.venv/bin/python')
   is rejected — it is a link to /opt/homebrew. Following the link first, then
   checking, is the whole trick; checking the string first would miss it.
   The model decides which paths to ask for, and it guesses (it will try
   "/proj/README.md" when it means "README.md"). Without this, one confident
   guess reaches ~/.ssh. This is the smallest possible version of the
   permission gate idea that a later module builds properly.

3. CAP THE OUTPUT. A file's contents and a directory listing both land in the
   transcript, and the transcript is resent in full on every turn. One
   `list_dir(".venv/lib")` without a cap can cost more context than the rest of
   the conversation combined.

4. SAY WHEN YOU TRUNCATED. If the model cannot tell that it only saw half a
   file, it will answer as though it saw all of it.
"""

