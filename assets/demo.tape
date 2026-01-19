# VHS Demo Script for researching-web skill
# https://github.com/charmbracelet/vhs

Output assets/demo.gif
Output assets/demo.webm

Set FontSize 14
Set Width 800
Set Height 450
Set Theme "Catppuccin Mocha"
Set Padding 20
Set TypingSpeed 50ms

# Start
Type "claude 'Research AI coding tools market 2025'"
Sleep 500ms
Enter
Sleep 800ms

# Progress output
Type@0ms `══════════════════════════════════════════════════════════`
Enter
Type@0ms `   RESEARCHING: "AI coding tools market 2025"`
Enter
Type@0ms `══════════════════════════════════════════════════════════`
Enter
Sleep 500ms

Type@0ms `[■■□□□□] Search: Exa 8 | Tabstack 5 → 10 unique`
Enter
Sleep 400ms

Type@0ms `[■■■□□□] Scoring: cbinsights.com (90), venturebeat.com (85)...`
Enter
Sleep 400ms

Type@0ms `[■■■■□□] Extracting: ✓✓✓✓✓ (5 sources parallel)`
Enter
Sleep 400ms

Type@0ms `[■■■■■□] Synthesizing + Verifying...`
Enter
Sleep 600ms

# Contradiction detection - the killer feature
Type@0ms ``
Enter
Type@0ms `⚠️  CONTRADICTION DETECTED:`
Enter
Type@0ms `   CB Insights: "Market 4B" vs SecondTalent: "Market 4.91B"`
Enter
Type@0ms `   → Different scope definitions`
Enter
Sleep 700ms

Type@0ms ``
Enter
Type@0ms `[■■■■■■] Confidence: 87%`
Enter
Type@0ms `         ├─ Consensus: 4/5 sources agree`
Enter
Type@0ms `         ├─ Freshness: 5/5 from 2024-2025`
Enter
Type@0ms `         └─ Contradictions: 2 found`
Enter
Sleep 400ms

# Research depth
Type@0ms ``
Enter
Type@0ms `📊 RESEARCH DEPTH: 5 pages | 64 facts | High coverage`
Enter
Sleep 400ms

Type@0ms `══════════════════════════════════════════════════════════`
Enter
Type@0ms `✓ GENERATED: insight-ai-coding-market-2025.html`
Enter
Type@0ms `══════════════════════════════════════════════════════════`
Enter

Sleep 2s
