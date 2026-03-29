---
name: daily
description: Generate a daily standup summary of work done the previous working day across all repos in ~/mcps
---

Generate a daily standup summary for the ~/mcps monorepo.

## Date logic

- Determine today's weekday.
- If today is **Monday**, the previous working day is **last Friday**.
- Otherwise, the previous working day is **yesterday**.

## Data collection

For each repo in ~/mcps (gps, wingfoil):

1. **Completed work** — commits from the previous working day:
   ```
   git -C ~/mcps/<repo> log --oneline --after="<prev_day> 00:00" --before="<today> 00:00" --all
   ```
2. **Work in progress** — uncommitted changes:
   ```
   git -C ~/mcps/<repo> status --short
   git -C ~/mcps/<repo> diff --stat HEAD
   ```

Skip a repo entirely only if it has zero commits and zero changes.

## Report format

Keep the report under 1 minute of spoken speech (~130 words max).

```
# Daily — <weekday>, <date>
*Previous working day: <prev_day_label>*

## <repo>
**Done:**
- <commit message trimmed to essential>

**In progress:** <1–2 sentences on staged/unstaged changes, or "nothing" if clean>

## Summary
<2 sentences max on overall activity across all repos>
```

## Save and display

Save the report to `~/mcps/docs/daily/<YYYY-MM-DD>.md` (create the directory if needed).
Print the report to the terminal using markdown rendering.
