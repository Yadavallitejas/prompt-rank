PromptRank
Design Assets & UI Guidelines Document
1. Design Philosophy
Core Feel

Dark, focused, technical

Minimal distractions

Data-dense but readable

Performance-oriented

Feels like a compiler, not a chatbot

If it looks like ChatGPT → it fails.
If it feels like an IDE + contest platform → it succeeds.

2. Layout System
Page Structure Model (Inspired by HackerRank)
4
Core Layout Grid

12-column responsive grid.

Primary zones:

Zone	Purpose
Header	Contest status + timer
Left Panel	Problem statement
Right Panel	Prompt editor
Bottom Panel	Submission results
Sidebar	Leaderboard / metrics
3. Global Design Tokens
Color System

Primary:

Background: #0F1115

Surface: #161B22

Elevated Surface: #1E2430

Accent:

Primary Action: #2F81F7

Success: #2EA043

Warning: #D29922

Error: #F85149

Leaderboard Highlight:

Gold: #E3B341

Silver: #8B949E

Bronze: #A371F7

Text:

Primary: #E6EDF3

Secondary: #8B949E

Muted: #6E7681

No gradients. Keep it sharp and serious.

Typography

Font Stack:

Headings: Inter / SF Pro

Code: JetBrains Mono / Fira Code

Numbers: Tabular numeric font for leaderboard

Hierarchy:

Level	Usage
H1	Contest title
H2	Problem title
H3	Section headings
Body	Problem description
Mono	Prompt editor + output
4. Core Screens
4.1 Dashboard
Purpose

User entry point.

Sections

Upcoming contests

Active contests

User rating card

Recent submissions

Global leaderboard snapshot

Rating Card Design

Display:

Current rating

Rank percentile

Rating trend (mini sparkline)

Strongest category

Keep it clean. No gamified nonsense.

4.2 Contest Page
Layout

Left: Problem Statement (scrollable)
Right: Prompt Editor
Top: Contest Header
Bottom: Submission Log

Contest Header

Includes:

Contest name

Countdown timer

Submission limit remaining

Allowed model (locked)

Fixed temperature indicator

The timer must be visually dominant.

Problem Statement Design

Structured sections:

Description

Input Format

Output Schema

Constraints

Scoring Details

Sample Input (non-eval)

Sample Output

Important:
Hidden testcases must never be visually hinted.

4.3 Prompt Editor Panel

This is the core UI.

Editor Features

Monaco Editor

Syntax highlighting (Markdown)

Line numbers

Word count

Token estimate preview

Auto-save draft

Submit button (fixed bottom)

Submission Button Behavior

Disabled if rate limit exceeded

Confirmation modal before submit

Show estimated evaluation cost

4.4 Submission Results Panel

Appears below editor after submission.

Status States

Queued

Running

Evaluated

Failed

After Evaluation

Display:

Final Score (large)

Score breakdown chart

Metric table

Expandable testcase logs

Tokens used

Latency average

Do not show hidden input.

4.5 Leaderboard Page
Layout

Columns:

| Rank | Username | Rating | Contest Score | Delta | Accuracy | Consistency |

Sorting enabled.

Highlight:

Current user row

Top 3 styled differently

Leaderboard Real-Time Behavior

WebSocket updates

Soft animation on rank change

No flashing or annoying effects

5. Component Design System
Buttons

Primary:

Filled accent color

Slight radius (6px)

No heavy shadows

Secondary:

Outlined

Subtle hover glow

Danger:

Red background

Confirmation modal required

Cards

Surface color #161B22

1px subtle border

Radius 8px

No heavy shadows

Tables

Dense rows

Monospaced numbers

Right-aligned numeric columns

Hover row highlight

6. UX Principles
6.1 Contest Mode Lockdown

During contest:

No editing past submissions

No external links

No copy of hidden logs

No API logs visible

After contest:

Detailed analytics unlocked

6.2 Feedback Design

Avoid:

“Great job!”

“Try again!”

Emotional language

Use:

Precise metrics

Structured feedback

Technical descriptions

Example:

Failure Type: Schema mismatch (missing key: tax_rate)

Not:

Something went wrong!

7. Responsive Design Rules

Desktop-first.

Tablet:

Problem collapsible.

Editor full width toggle.

Mobile:

View-only mode.

No contest participation allowed on mobile (MVP decision).

8. Microinteractions

Timer color changes under 5 minutes.

Score counter animates upward.

Submission state spinner minimal.

Rank changes slide smoothly.

Avoid flashy animations.

9. Iconography

Use:

Minimal line icons.

Feather or Lucide icons.

No filled cartoon icons.

Key icons:

Trophy

Clock

Shield (for robustness)

Lightning (efficiency)

Graph (consistency)

10. Empty States

If no submissions:

“No submissions yet.”

Not motivational quotes.

If no contests:

“No active contests. Check upcoming schedule.”

11. Branding Guidelines

Logo concept:

Minimal wordmark.

Subtle “rank graph” arrow integrated into R.

Do not use:

Hacker visuals

Matrix themes

Green-on-black cliché

This is engineering competition, not movie cosplay.

12. Accessibility

Contrast ratio ≥ 4.5

Keyboard navigation fully supported

Screen reader labels on metrics

Tab navigation in editor

13. Figma Design Asset Structure

Organize:

Tokens (colors, typography)

Components (buttons, cards, tables)

Layout templates

Page prototypes

Interaction states

Naming convention:

PR/Button/Primary
PR/Table/Leaderboard
PR/Card/Rating
PR/Layout/Contest
14. What Makes This UI Different from HackerRank

HackerRank evaluates code correctness.

PromptRank evaluates:

Variance

Determinism

Efficiency

Multi-run stability

So we must visualize:

Metric breakdowns

Variance charts

Token usage bars

Stability indicators

This is where you differentiate.

15. Advanced Future UI Extensions

Compare two submissions side-by-side

Variance heatmap per testcase

Prompt diff viewer

Performance over time graph

Category-based ratings+
