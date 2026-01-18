# VHS Demo Script for researching-web skill
# https://github.com/charmbracelet/vhs

Output assets/demo.gif
Output assets/demo.webm

Set FontSize 14
Set Width 800
Set Height 500
Set Theme "Catppuccin Mocha"
Set Padding 20
Set TypingSpeed 50ms

# Start
Type "claude 'Research AI coding tools market 2025'"
Sleep 500ms
Enter
Sleep 1s

# Progress output
Type@0ms `══════════════════════════════════════════════════════`
Enter
Type@0ms `   RESEARCHING: "AI coding tools market 2025"`
Enter
Type@0ms `══════════════════════════════════════════════════════`
Enter
Sleep 800ms

Type@0ms `[■■□□□□] Search: Exa 8 | Tabstack 5 → 10 unique`
Enter
Sleep 600ms

Type@0ms `[■■■□□□] Scoring: cbinsights.com (90), venturebeat.com (85)...`
Enter
Type@0ms `         Selected: 5 sources above threshold`
Enter
Sleep 600ms

Type@0ms `[■■■■□□] Extracting (parallel)...`
Enter
Sleep 300ms
Type@0ms `         ✓ cbinsights.com`
Enter
Sleep 200ms
Type@0ms `         ✓ venturebeat.com`
Enter
Sleep 200ms
Type@0ms `         ✓ digitalapplied.com`
Enter
Sleep 200ms
Type@0ms `         ✓ index.dev`
Enter
Sleep 200ms
Type@0ms `         ✓ secondtalent.com`
Enter
Sleep 600ms

Type@0ms `[■■■■■□] Synthesizing + Verifying...`
Enter
Sleep 800ms

# Contradiction detection - the killer feature
Type@0ms ``
Enter
Type@0ms `⚠️  CONTRADICTION DETECTED:`
Enter
Type@0ms `   CB Insights: "Market size 4B"`
Enter
Type@0ms `   SecondTalent: "Market 4.91B in 2024"`
Enter
Type@0ms `   → Likely cause: different scope definitions`
Enter
Sleep 1s

Type@0ms ``
Enter
Type@0ms `[■■■■■■] Confidence: 87%`
Enter
Type@0ms `         ├─ Consensus: 4/5 agree`
Enter
Type@0ms `         ├─ Top source: 90 (CB Insights)`
Enter
Type@0ms `         ├─ Freshness: 5/5 from 2024-2025`
Enter
Type@0ms `         └─ Contradictions: 2 found`
Enter
Sleep 500ms

# Research depth - Mira's feature
Type@0ms ``
Enter
Type@0ms `📊 RESEARCH DEPTH`
Enter
Type@0ms `   Pages analyzed: 5 | Facts extracted: 64`
Enter
Type@0ms `   Sources: 5 (1 premium, 1 news, 3 industry)`
Enter
Type@0ms `   Coverage: High`
Enter
Sleep 500ms

Type@0ms `══════════════════════════════════════════════════════`
Enter
Type@0ms `✓ READY: insight-ai-coding-market-2025.html`
Enter
Type@0ms `══════════════════════════════════════════════════════`
Enter

Sleep 2s
