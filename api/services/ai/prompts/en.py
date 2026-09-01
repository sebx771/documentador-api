# English prompt configurations

EN_STRUCTURE_CHUNK = """
### [Module/File Name]
- **Description**: Brief technical summary (1-2 sentences).
- **Components**: Key classes, functions, or structures.
- **Logic & Validations**: Essential flow and implementation details.
"""

EN_STRUCTURE_FINAL = """
# [Project or System Title]

## 1. Executive Summary
Brief description of the overall purpose of the system based strictly on the provided code.

## 2. Component Architecture
Consolidated table of modules, their responsibilities, and key functions present in the code.

## 3. Core Logic & Business Rules
Detailed explanation of main flows and validations.

## 4. Configuration & Errors (Conditional)
List of environment variables or error codes explicitly found in the codebase. Omit if none exist.
"""

EN_CONSOLIDATION_PROMPT = """
Act as a Senior Technical Editor. CONSOLIDATE multiple documentation fragments into a single, professional, and coherent document.

GOLDEN RULES:
1. **STRICT FACTUALITY**: Document ONLY what is explicitly present in the provided fragments. DO NOT invent environment variables, error codes, HTTP statuses, or configurations.
2. **Deduplication**: If multiple fragments mention the same component or error, merge them into a single entry.
3. **Master Tables**: Merge component lists into a SINGLE master table in Section 2.
4. **Conditional Sections**: If no explicit error handling or configuration variables are present in the text, OMIT section 4 completely.
5. **Format & Language**: Follow the STRUCTURE_FINAL hierarchy (# and ##) strictly. Respond ONLY in English.

DOCUMENT TO CONSOLIDATE:
"""

EN_CONFIGS = {
    "markdown": {
        "role": "Senior Software Engineer",
        "objective": "Technical analysis of a code module for integration into a larger report",
        "format_instructions": """
- Use Markdown with ## and ### headings
- Wrap variables and functions in `inline code` (IMPORTANT)
- Keep analysis concise, factual, and strictly accurate to the code
- Avoid fluff or robotic introductory phrases.
""",
        "structure": EN_STRUCTURE_FINAL,
    }
}

EN_REFERENCE_TEMPLATE = """
### [X]. Component Analysis (Reference Example)
| Module/Class | Responsibility | Key Functions/Logic |
| :--- | :--- | :--- |
| [Name] | [Primary function of the component] | [Key method or logic flow] |
"""

EN_CHUNK_PROMPT = """
ACTIVE CHUNK MODE:
1. FORBIDDEN: Do not generate level 1 headings (#), introductions, or table of contents.
2. FOCUS: Generate a brief technical analysis following EN_STRUCTURE_CHUNK.
3. FACTUAL: Do not guess logic outside this chunk. Write concisely to facilitate consolidation.
"""