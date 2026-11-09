---
name: review-contributions
description: Maintainer-side review of incoming pull requests to the shared house repo - list open PRs, run the contribution gate on each, have the pr-reviewer agent review the diff, and draft a review the maintainer approves. Use on "/review-prs", "review the open PRs", or when a PR notification arrives.
---

# Review contributions (maintainer)

1. `gh pr list --repo <upstream> --state open` (the upstream is in `house.json`). For each PR: `gh pr checkout <n>` in a throwaway clone or worktree, never in your working copy.
2. Run `python3 ledger/contribute.py check --base origin/main` there. A blocked PR gets a short, kind comment listing the exact lines to remove; do not merge it.
3. Dispatch `pr-reviewer` (haiku) with the diff. **Verify its top 3 findings yourself** before relaying them; it can be wrong.
4. Draft the review comment (verdict, blockers, minors). **Show it to the maintainer; posting a comment or merging is their click**, never automatic.
5. After a merge, tell the contributor's agent nothing: their next `git fetch upstream` brings it in. Note the lesson in `ledger/LEARNINGS.md` if the PR taught the process something.
Never merge a PR that touches `.github/`, hooks, the install guard, the isolation check or a ship gate without reading every line.
