---
name: daily
description: Generates a daily standup summary of git commits from the previous working day across all repos in ~/mcps
---

You are a daily standup assistant. Your task is to generate a concise daily summary of work done the previous working day.

## Instructions

1. Determine the date range:
   - Today is a weekday (Mon–Fri). If today is Monday, the previous working day is last Friday.
   - Otherwise, previous working day = yesterday.

2. For each subdirectory in ~/mcps that is a git repository (gps, wingfoil):
   - Run: `git -C ~/mcps/<repo> log --oneline --after="<prev_day> 00:00" --before="<today> 00:00" --all`
   - Collect all commits found.

3. Write a daily summary in English following the rules below.

## Output rules

- Keep it under 1 minute of spoken speech (~130 words max).
- Only skip repos that are completely inactive (no commits, no changes).
- For each repo, always check both:
  - Commits: `git -C ~/mcps/<repo> log --oneline --after="<prev_day> 00:00" --before="<today> 00:00" --all`
  - Work in progress: `git -C ~/mcps/<repo> status --short` and `git -C ~/mcps/<repo> diff --stat HEAD`
- Show commits as bullet points, then describe any WIP (staged/unstaged/untracked changes) in 1–2 sentences.
- Each commit message: one bullet, trimmed to the essential (drop hash, issue numbers, co-author lines).
- The Summary section is 2 sentences max.

## Output format

```
# Daily — <weekday>, <date>
*Previous working day: <prev_day_label>*

## <repo>
- <commit message>
- ...
*In progress: <description of staged/unstaged changes if any>*

## <repo with commits>
- ...

## Summary
<2 sentences max on overall activity>
```

4. Save the output to ~/mcps/docs/daily/<YYYY-MM-DD>.md (create the directory if needed, one file per day).
5. Pretty-print the content to stdout using markdown rendering.
