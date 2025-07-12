# Systematic Review Automator

A lightweight Python GUI tool to **automate article screening** for systematic reviews using OpenAI's GPT models. This tool helps classify articles based on predefined exclusion criteria and outputs decisions with reasoning.

---

## Features

- Drag-and-drop CSV file support  
- Real-time progress bar and elapsed time tracking  
- GPT-powered classification using `gpt-4o-mini`  
- CSV export with classification, criteria, and justification

---

## Input Format

The input CSV file should contain the following columns:

- `title`
- `author`
- `year`
- `abstract`

Example:

| title                          | author       | year | abstract              |
|-------------------------------|--------------|------|------------------------|
| Effect of Drug A on Outcome B | Smith et al. | 2022 | This study investigates... |

---

## Exclusion Criteria

The model excludes articles based on the following:
1) Animal study(research conducted on non-human animals): 
2) Research category belongs to congress, erratum, letter, note, narrative review meaning that study that is not original study.
3) Articles related with retraction or belongs to grey literature.
4) The research is not written in Korean or English (this should be based explicitly on the title or abstract indicating the language is neither Korean nor English). 
5) Systematic review.
6) Any case study, and case series.


---
