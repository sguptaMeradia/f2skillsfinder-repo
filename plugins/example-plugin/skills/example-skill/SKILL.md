---
name: example-skill
description: Turns rough meeting notes into a short recap with decisions, owners and dates. Use when someone pastes meeting notes and asks for a recap, summary or action list.
---

# Example skill: meeting notes to recap

This is a template. Replace the content, keep the shape.

## When this skill runs

- The person pastes or attaches meeting notes and asks for a recap, summary or action list.
- Not for transcripts longer than about an hour; say so and ask which part to cover.

## Steps

1. Read the notes once. List every decision, every action item and every date mentioned.
2. For each action item, record the owner exactly as written. If no owner is named, write "Owner: not stated". Never guess.
3. Write the recap in this order:
   - **Decisions** (one line each)
   - **Actions** (owner, task, due date)
   - **Open questions**
4. Keep every name, number and date exactly as the notes give them.

## Output

Plain text in the reply, under 200 words unless the person asks for more.

## Supporting files

Put reference material the skill needs (templates, examples, lookup tables) in this folder
next to SKILL.md and point to it from the steps above, for example `references/recap-example.md`.
