# Systematic Review Automator

A lightweight Python GUI tool to **automate article screening** for systematic reviews using OpenAI's GPT models. This tool helps classify articles based on predefined exclusion criteria and outputs decisions with reasoning.

---

## ✅ Features

- Drag-and-drop CSV file support  
- Real-time progress bar and elapsed time tracking  
- GPT-powered classification using `gpt-4o-mini`  
- CSV export with classification, criteria, and justification

---

## 📁 Input Format

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

## 🚫 Exclusion Criteria

The model excludes articles based on the following:

1. Animal study (non-human subjects)  
2. Non-original articles (e.g., congress, letter, note, narrative review)  
3. Retracted or grey literature  
4. Not written in **Korean or English**  
9. Systematic review  
10. Case study or case series  

> ⚠️ **Criteria numbers 5, 6, 7, 8 do not exist** and are never used.

---
