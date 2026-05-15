# Segmentation Codebook: Chinese Students Educated in the United States / Study Abroad Corpus

## Goal

For each newspaper document, delineate the **largest semantic unit** that contains the relevant study-abroad material and its coherent context, while excluding unrelated neighboring items caused by OCR/OLR segmentation problems or newspaper brevity columns.

This is not sentence-level keyword extraction. The goal is to recover the article/item that a historian would cite as the relevant newspaper unit.

## Key principle: largest coherent relevant unit

Keep **all and only** the continuous textual unit that forms a coherent story around Chinese study abroad, American-educated Chinese, returned students, foreign-educated Chinese professionals, scholarships, loans, educational missions, or related institutions.

When the whole article is about a larger subject and the study-abroad topic is mentioned only in passing, keep the **entire article**, because the mention may be analytically meaningful in its full political/social context.

When the document is actually a cluster of unrelated brief items, keep only the item(s) related to the corpus topic.

## Relevant topic scope

A passage is relevant if it concerns any of the following:

1. Chinese students educated in the United States.
2. Chinese students studying abroad generally.
3. Returned students or returned-student organizations.
4. American-educated, European-educated, Japanese-educated, or otherwise foreign-educated Chinese.
5. Chinese professionals whose authority, politics, career, or conflict is linked to foreign education.
6. Study-abroad funding, scholarships, loans, Boxer Indemnity remissions, government missions, or institutions sending students abroad.
7. Public debates about Western education, foreign degrees, returned students, or overseas-educated elites in China.

## Main segmentation classes

### WHOLE_DOCUMENT

Use when the whole document is a coherent article, letter, editorial, review, or report and the relevant material belongs to that whole argument/story.

Use WHOLE_DOCUMENT even if the study-abroad issue is brief or appears in passing, when the article is otherwise coherent.

Examples:
- A long political editorial mentioning American-educated liberals in China.
- A biography where American education is one component of the person’s career.
- A report on Chinese politics that briefly contrasts Japan-educated and America-educated leaders.

### SINGLE_SEGMENT

Use when the document contains several unrelated items, but only one continuous item concerns the topic.

Typical cases:
- Brevities columns.
- Local news columns.
- Personal notes columns.
- “News in brief” or “Chinese news” miscellanies.
- OCR/OLR wrongly joins multiple articles with unrelated headlines.

Example:
- A document begins with “Boxer Indemnity Remission,” then continues with unrelated Trade Marks Bureau, Presidential Orders, and Minister to London items. Keep only the Boxer Indemnity Remission item.

### MULTIPLE_SEGMENTS

Use when a document contains more than one separated relevant item. Return each relevant segment separately, preserving order.

Example:
- A brevities column includes one item on returned students and another item on scholarships, separated by unrelated local news.

### NO_RELEVANT_SEGMENT

Use only when the classifier marked or the segmenter determines the document has no relevant study-abroad content.

## Boundary rules

### Start boundary

Start at the nearest heading, dateline, bullet, dash, or paragraph opening that introduces the relevant semantic unit.

If there is no clear heading, start at the sentence where the coherent relevant item begins.

### End boundary

End before the next unrelated heading, item, dateline, bullet, or abrupt topic shift.

Common signs of a new unrelated item:
- A new title or headline in title case.
- A dash-led note about a different subject.
- “Latest Presidential Orders,” “Trade Marks Bureau,” “Personal Notes,” etc.
- Sudden change from education topic to appointments, railway, crime, weather, shipping, advertisements, or diplomacy unrelated to education.

### Context inclusion

Include enough surrounding context to make the item intelligible:
- headline or subheading;
- dateline or location if attached to the item;
- named actors and institutions;
- preceding sentence if it sets up the relevant reference;
- following sentence if it explains the consequence or meaning.

Do not include unrelated surrounding items merely because they appear in the same ProQuest/OCR document.

## Special cases

### Passing mention inside coherent long article

If the study-abroad point appears inside an otherwise coherent article, keep the whole article. Do not cut out only the mention.

Reason: the full article is the semantic unit.

### Improperly segmented OCR/OLR documents

If the OCR document clearly joins multiple unrelated newspaper items, identify the relevant item-level unit(s). Ignore unrelated items before and after.

### Brevities / personal news / local news

Treat each brief as its own article-like unit. Keep relevant briefs only.

### Returned-student associations

Keep the item about the association, including meeting details, speakers, officers, and stated purpose.

### Foreign-educated doctors or professionals

Keep the item describing the dispute, appointment, credentials, professional conflict, or public debate. Include enough context to understand the professional field and conflict.

### Loans, scholarships, indemnity, missions

Keep the item about funding or institutional arrangements for study abroad, even if Britain, Europe, Japan, or general foreign study is involved rather than the United States specifically.

## Output fields

The segmenter should return structured JSON:

- `segmentation_label`: one of `WHOLE_DOCUMENT`, `SINGLE_SEGMENT`, `MULTIPLE_SEGMENTS`, `NO_RELEVANT_SEGMENT`.
- `keep_entire_document`: true/false.
- `segments`: list of segment objects.
- Each segment object:
  - `segment_index`: integer starting at 1.
  - `segment_title`: short title or inferred title.
  - `start_anchor`: exact short phrase near segment beginning.
  - `end_anchor`: exact short phrase near segment end.
  - `segment_text`: extracted text.
  - `topic_type`: one of `US_EDUCATED_CHINESE`, `STUDY_ABROAD_GENERAL`, `RETURNED_STUDENTS`, `FOREIGN_EDUCATED_PROFESSIONALS`, `SCHOLARSHIP_LOAN_POLICY`, `OTHER_RELATED`.
  - `relevance_to_original_topic`: `HIGH`, `MEDIUM`, or `LOW`.
  - `boundary_confidence`: number from 0 to 1.
  - `boundary_rationale`: concise explanation.
  - `excluded_content_summary`: concise summary of excluded unrelated content, if any.

## Quality control

Flag for manual review when:
- `boundary_confidence < 0.75`;
- the segmenter returns `MULTIPLE_SEGMENTS`;
- the original document is very long and the retained segment is very short;
- start/end anchors cannot be found exactly in the original text;
- the model says the item boundary is uncertain.

## Few-shot guidance

### Example A: Boxer Indemnity in mixed news column

Input pattern: “Boxer Indemnity Remission … [discussion of remission movement] … Tientsin Trade Marks Bureau … Latest Presidential Orders …”

Output: `SINGLE_SEGMENT`; keep only “Boxer Indemnity Remission” item.

Rationale: the later sections are unrelated brief news items.

### Example B: American-educated liberals inside political letter

Input pattern: a coherent letter about Chinese politics and the Kuomintang, with repeated mentions of American-educated liberals.

Output: `WHOLE_DOCUMENT`.

Rationale: the education references belong to the whole argument.

### Example C: Foreign-educated doctors dispute

Input pattern: one item describes a dispute between foreign-educated doctors and Chinese doctors, surrounded by unrelated local news.

Output: `SINGLE_SEGMENT`; keep the doctors item only.

Rationale: foreign-educated Chinese professionals are part of the broader overseas-education ecosystem.

### Example D: Returned Students’ Union meeting

Input pattern: meeting notice or report of Euro-American Returned Students’ Union.

Output: `SINGLE_SEGMENT` if in a mixed column; `WHOLE_DOCUMENT` if the whole document is only that report.

Rationale: returned-student organization is relevant study-abroad context.
