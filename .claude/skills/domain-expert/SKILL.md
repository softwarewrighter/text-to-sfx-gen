---
name: domain-expert
description: "Acquire real working competence in an unfamiliar domain BEFORE producing domain-heavy work, using an aggressive, multi-layered search doctrine (semantic, keyword, and primary literature retrieval). You must immortalize this research as a dated, sourced, reusable domain briefing. This skill prevents the dangerous failure mode of \"fluent shallow competence\"—where you produce plausible but technically flawed output. Use whenever a task leans on a specialized field you don't know cold—one with its own vocabulary, canon, standards, tools, or practitioners—where confident-but-shallow output is worse than useless. Trigger before writing, designing, coding, or advising in a niche domain. Your mandate is to become an absolute expert at all things related to the one task or goal, equipping yourself with the *right* answer, grounded in verifiable truth, directly read from primary texts, and explicitly cited—never just read *about* via secondary summaries."
---
# Skill: Domain Expert

## The Prime Use Case: MIR & EDM Code Rigor

Consider building a Music Information Retrieval (MIR) tool to detect audio "stutters and chops" in Electronic Dance Music. A shallow, zero-research pass will hallucinate a generic audio analysis script that utterly fails on real samples. `Domain Expert` prevents this by stopping the build, diving into the academic literature for MIR onset detection (e.g., convolutional networks for spectral flux), reading the actual mathematical methodologies, and applying those exact algorithms to the code. By establishing the ground truth first, you generate perfectly validated samples that pass 10/10 times, closing the bug immediately.

## The Trigger & Tripwires

Fire this skill *before* the work starts. Treat any of these as a tripwire to stop and brief yourself first:

* The task lives in a field with its own terms of art, named methods, standards, or canon.


* You catch yourself reaching for an analogy from an adjacent domain to cover a knowledge gap.


* There is a community of practitioners who would instantly read your work as amateur.


* The task is load-bearing, and shipping a "plausible but wrong" implementation is costly.


* The user treats you as an expert in something you only have surface knowledge of.



## The Acquisition Target: V-C-P-F

Do not just collect scattered facts; collect the four pillars that separate a true practitioner from a fluent outsider:

* **Vocabulary:** The field's real terms of art. Without these, you search like an outsider and signal yourself as one.


* **Canon:** The load-bearing primary sources, official standards, seminal papers, reference tools, and absolute authorities.


* **Pitfalls:** What actual practitioners know that outsiders constantly get wrong—the deprecated approaches and subtle traps.


* **Frontier:** What is current or newly changed in the field, especially past standard training cutoffs.



## Deep Search Doctrine (Beyond Keyword & Semantic)

Run these search modes sequentially to build unshakeable competence:

1. **Phase 1: Semantic / Conceptual Search:** Map the territory using natural-language queries to learn the core concepts, discover the vocabulary, and identify the field's authorities. You cannot search like an insider until you learn their words.


2. **Phase 2: Keyword / Exact-Term Search:** Query the exact terms of art, standard numbers, method names, and primary-source titles you just uncovered. This finds the specific canonical documents.


3. **Phase 3: Primary Literature & Code Extraction:** Bypass aggregators entirely. Search for and retrieve the actual research papers (e.g., arXiv PDFs), raw datasets, or repository source code. Read the methodology firsthand. If a claim rests on a single blog, it is provisional until an independent, primary authority agrees.



## The Expert-Enough Gate

You are only done when the briefing passes every test below, and each pass *must cite the evidence that satisfies it*:

* **Vocabulary Test:** You can correctly *use* the field's terms of art, not just paraphrase them.


* **Canon Test:** Every load-bearing claim traces back to a primary/authoritative source.


* **Pitfall Test:** You surfaced the well-known traps a practitioner warns newcomers about.


* **Transfer Test:** Another instance could complete the task perfectly using only your briefing, without redoing the research.



## The Briefing Artifact (Immortalization)

Save the briefing to `docs/briefings/<topic>-YYYY-MM-DD.md` (kebab-case topic, compile date), creating the directory if needed. Before researching, check `docs/briefings/` and `docs/research-findings.md` for an existing briefing on the topic and extend it rather than starting over. Tell the user the file path when done.

```text
# Domain briefing — <field / sub-topic>   (compiled YYYY-MM-DD, for task: <task>)

**Confidence & ceiling:** <how deep this goes; what it does NOT cover; recheck-frontier date>

## Vocabulary — terms of art
- <term> — <meaning, in the field's own usage>   [source]

## Canon — the load-bearing sources
- <standard / paper / tool> — <why it's canonical>   [primary URL]

## Pitfalls — what practitioners know that outsiders get wrong
- <the trap> — <why the obvious move is wrong>   [source]

## Frontier & Ground Truth Methodologies
- <finding/method>   [direct primary source, dated]

## Open gaps — what search couldn't establish
- <gap> — <recommended way to close it: expert / primary text / labeled uncertainty>

```
