# Codebook: Chinese students educated in the United States newspaper corpus

## Research goal

Build an exhaustive historical newspaper corpus on **Chinese students educated in the United States**, while preserving a broader contextual layer on Chinese study abroad, returned students, and foreign-educated Chinese people.

## Main revision in v4

The boundary between `HIGHLY_RELEVANT_US_CHINESE_STUDENTS` and `LESS_RELEVANT_STUDY_ABROAD_GENERAL` is now **actor-based as well as topic-based**.

An article should be classified as **highly relevant** whenever it mentions an identifiable **American-educated Chinese person**, **American-returned student**, **U.S.-educated Chinese group**, or **Chinese student connection to American institutions**, even if the article's main topic is not education itself.

This means that post-return careers, appointments, meetings, dinners, public speeches, organizational activities, political conflicts, professional roles, local news, and personal news can all be **highly relevant** if an American-educated Chinese actor appears in the article.

## Unit of analysis

One newspaper article row. Use all available metadata and text together: `DocId`, `Title`, `Date`, `Source`, and `Text`.

## Labels

### A. `HIGHLY_RELEVANT_US_CHINESE_STUDENTS`

Use this label when the article contains Chinese people, students, pupils, scholars, graduates, professionals, officials, reformers, educational missions, returned students, or returned-student organizations whose education, training, or identity is explicitly connected to the **United States / America / American institutions**.

#### Core rule

Classify as `HIGHLY_RELEVANT_US_CHINESE_STUDENTS` if the article contains:

1. a Chinese person, group, student, professional, official, returned student, or returned-student organization; and
2. an explicit U.S./American education, training, institution, or return-from-America cue.

The article does **not** need to focus primarily on education. The U.S.-educated Chinese actor only needs to be meaningfully present.

#### Inclusion criteria

Classify as HIGH when the article mentions any of the following:

1. **Chinese students in America / the United States**
   - Chinese students studying in America.
   - Chinese students sent to America.
   - Chinese students returning from America.
   - Chinese students at American schools, colleges, or universities.

2. **American-educated or American-returned Chinese people**
   - American-educated Chinese officials, magistrates, diplomats, doctors, engineers, teachers, reformers, merchants, soldiers, activists, or public figures.
   - American-returned students mentioned in relation to later careers, offices, appointments, social roles, speeches, elections, public activities, or organizational work.
   - Example: DocId `1322117985`, an American-returned student who is now a magistrate and elected head of the Merchant Volunteer Corps in Canton.

3. **U.S.-educated Chinese alongside other foreign-educated Chinese**
   - Articles comparing American-educated Chinese with Japanese-, British-, European-, or other foreign-educated Chinese.
   - Articles where American-returned students appear as one group among other returned students.
   - Example: DocId `1371519349`, persecution of American-educated liberals contrasted with Japanese-educated officials.

4. **Mixed Euro-American returned-student organizations or events**
   - Meetings, dinners, lectures, elections, banquets, or activities of organizations such as the Euro-American Returned Students' Union when American-returned students are named, discussed, or clearly part of the organization/event.
   - Example: DocId `1759709613`, Euro-American Returned Students' Union meeting/dinner, if American-returned students are actors in the organization or event.

5. **American institutions or organizations connected to Chinese students**
   - Yale, Harvard, Columbia, Cornell, Michigan, Wisconsin, MIT, Stanford, University of California, or other American institutions, when connected to Chinese students or Chinese graduates.
   - Chinese Students' Alliance, Chinese Students' Christian Association, Chinese student clubs in America.

6. **U.S.-specific scholarships or educational missions**
   - Boxer Indemnity scholarships specifically sending Chinese students to the United States.
   - Educational missions to America.
   - U.S.-specific preparatory or selection programs.

#### Typical positive signals

- Chinese student in America; Chinese students in the United States.
- American-educated Chinese; American-trained Chinese; American-returned student.
- returned from America; educated in America; graduate of an American university.
- Chinese graduate of Yale/Harvard/Columbia/Cornell/Michigan/Wisconsin/MIT/Stanford/University of California, etc.
- American-educated liberals; American-returned officials; American-trained doctors.
- Euro-American returned students, when American-returned students are part of the story.

#### Important note

Do **not** downgrade to LESS merely because:

- the article also discusses Japanese-, British-, European-, or other foreign-educated Chinese;
- the American-educated Chinese person is mentioned as part of a larger group;
- the article is mainly about the person's post-return career;
- the article appears in local news, personal news, brevities, or social-event sections.

If an American-educated Chinese actor is meaningfully present, classify HIGH.

---

### B. `LESS_RELEVANT_STUDY_ABROAD_GENERAL`

Use this label when the article concerns the broader ecosystem of **Chinese overseas education, study abroad, returned students, foreign-educated Chinese professionals, or institutions/policies/funding that support study abroad**, but it does **not** contain an explicit American/U.S.-educated Chinese actor, group, institution, or student connection.

This category remains broad and contextual, but it is no longer the right label for articles that clearly mention American-educated Chinese people.

#### Core rule

If the article concerns Chinese study abroad or returned students generally, classify it as at least LESS. If an American/U.S.-educated Chinese person or group appears, upgrade to HIGH.

#### Inclusion criteria

Classify as LESS when the article is about any of the following, without a U.S.-specific Chinese actor or institution:

1. **Returned-student organizations without clear American-returned actors**
   - Meetings, elections, speeches, banquets, lectures, publications, memorials, or public activities of returned-student associations where the country of education is unspecified or non-U.S.

2. **Foreign-educated Chinese professionals, country unspecified or non-U.S.**
   - Disputes, credentials, appointments, status conflicts, or institutional debates involving Chinese professionals educated abroad.
   - Includes doctors, engineers, lawyers, teachers, officials, diplomats, military officers, scientists, and reformers trained abroad.
   - If they are American-educated/American-returned, classify HIGH instead.

3. **Study-abroad policy, finance, and infrastructure**
   - Loans, scholarships, grants, indemnity funds, government appropriations, selection exams, preparatory schools, educational missions, or administrative systems for sending Chinese students abroad.
   - Example: DocId `1416504625`, British loan for study abroad.

4. **Non-U.S. Chinese study abroad**
   - Chinese students in Britain, Europe, Japan, France, Germany, Russia, or other countries.
   - Articles about Chinese students abroad generally, with no American/U.S. destination or actor.

5. **Returned students with unspecified or mixed foreign education**
   - “Foreign returned students,” “returned scholars,” “students returned from abroad,” or similar phrases, if no American-returned or U.S.-educated Chinese actor is identifiable.

6. **Boxer Indemnity and other scholarship systems**
   - Generic or non-U.S.-specific articles about the Boxer Indemnity, scholarships, or remitted funds for Chinese education abroad.
   - U.S.-specific Boxer Indemnity articles should be HIGH.

#### Typical positive signals

- returned students, returned scholars, foreign returned students.
- students abroad, study abroad, overseas students, foreign education.
- returned students' union, returned students' association.
- foreign-trained doctors/professionals, foreign-educated Chinese, Western-trained professionals.
- scholarships, loans for study abroad, indemnity scholarships, educational mission, government sends students abroad.
- Chinese students in Britain, Europe, Japan, France, Germany, Russia, or “foreign countries.”

---

### C. `IRRELEVANT`

Use this label when the article does not meaningfully concern Chinese overseas education, returned students, study-abroad policy, or foreign-educated Chinese people.

#### Inclusion criteria

Classify as IRRELEVANT when the article is mainly about:

- Americans returning to or from China, America, Europe, or another place, with no Chinese study-abroad angle.
- Non-Chinese people educated in America.
- Foreigners, missionaries, diplomats, tourists, merchants, soldiers, or athletes in China with no Chinese education/study-abroad angle.
- Generic politics, commerce, war, travel, shipping, sports, crime, society news, or diplomacy with no Chinese overseas education content.
- OCR false positives where “Chinese,” “student,” “America,” “foreign,” or “returned” appear incidentally or in unrelated contexts.
- Foreign professionals in China who are not Chinese returned students or foreign-educated Chinese people.

#### Important caution

Do **not** classify as IRRELEVANT merely because the article lacks a U.S. connection. If it concerns Chinese study abroad, returned students, or foreign-educated Chinese professionals, use LESS. If it mentions American-educated Chinese people, use HIGH.

## Decision rules

1. **First ask: Does the article mention an American-educated Chinese person, American-returned student, U.S.-educated Chinese group, or Chinese student connection to America?**
   - If yes, classify HIGH.

2. **Apply the actor-based HIGH rule broadly.**
   - HIGH applies even when the article is mainly about post-return career, local office, professional activity, political role, meeting, dinner, public speech, social news, or an organizational event.

3. **Mixed foreign-education rule.**
   - If American-educated Chinese appear alongside Japanese-, British-, European-, or other foreign-educated Chinese, classify HIGH.
   - Do not downgrade to LESS because the article is comparative or mixed.

4. **Returned-student organization rule.**
   - If a returned-student organization clearly includes or mentions American-returned Chinese actors, classify HIGH.
   - If the organization is returned-student related but the American connection is absent or unclear, classify LESS.

5. **Post-return career rule.**
   - Any article mentioning an American-educated Chinese person’s later office, position, career, association, social activity, or public role is HIGH.

6. **General study-abroad rule.**
   - If there is no American/U.S.-educated Chinese actor, but the article concerns Chinese overseas education, returned students, foreign-educated Chinese professionals, scholarships, loans, or study-abroad policy, classify LESS.

7. **Boxer Indemnity rule.**
   - U.S.-specific student content: HIGH.
   - Generic or non-U.S. study-abroad student content: LESS.
   - No meaningful student/education content: IRRELEVANT.

8. **Ambiguity/OCR rule.**
   - If OCR is poor but there are credible clues for American-educated Chinese, use HIGH with lower confidence and `needs_review=true`.
   - If OCR is poor but there are credible clues for Chinese overseas education generally, use LESS with lower confidence and `needs_review=true`.
   - If OCR is poor and no reliable education-related clue exists, use IRRELEVANT with `needs_review=true`.

9. **When in doubt between HIGH and LESS.**
   - Choose HIGH if any identifiable Chinese actor/group is linked to American/U.S. education, training, institutions, or return from America.

10. **When in doubt between LESS and IRRELEVANT.**
   - Choose LESS if there is any meaningful evidence of Chinese study abroad, returned students, foreign education, or foreign-educated Chinese professionals.

## Output fields

Return one JSON object with:

- `label`: one of `HIGHLY_RELEVANT_US_CHINESE_STUDENTS`, `LESS_RELEVANT_STUDY_ABROAD_GENERAL`, `IRRELEVANT`
- `confidence`: number from 0.0 to 1.0
- `rationale`: 1-2 concise sentences explaining the decisive evidence
- `evidence_terms`: short list of decisive phrases or terms found in the article/metadata
- `needs_review`: true if confidence is below 0.70, OCR is garbled, or the article plausibly mixes categories

## Calibration examples

```json
{
  "doc_id": "1371519349",
  "label": "HIGHLY_RELEVANT_US_CHINESE_STUDENTS",
  "reason": "The article discusses American-educated liberals in China and contrasts them with Japanese-educated officials. Mixed foreign-education comparison does not reduce relevance when American-educated Chinese actors are present."
}
```

```json
{
  "doc_id": "1759709613",
  "label": "HIGHLY_RELEVANT_US_CHINESE_STUDENTS",
  "reason": "The article concerns a Euro-American Returned Students' Union event where American-returned students are part of the organization/event. U.S.-educated actors embedded in a mixed returned-student organization count as highly relevant."
}
```

```json
{
  "doc_id": "1322117985",
  "label": "HIGHLY_RELEVANT_US_CHINESE_STUDENTS",
  "reason": "The article mentions an American-returned student in relation to his post-return career as magistrate and head of the Merchant Volunteer Corps. Post-return activity of an American-educated Chinese person is highly relevant."
}
```

```json
{
  "example": "Dispute between foreign-educated doctors and Chinese doctors, country unspecified",
  "label": "LESS_RELEVANT_STUDY_ABROAD_GENERAL",
  "reason": "This concerns the status of foreign-educated Chinese professionals but lacks an American/U.S.-education cue."
}
```

```json
{
  "doc_id": "1416504625",
  "label": "LESS_RELEVANT_STUDY_ABROAD_GENERAL",
  "reason": "The article concerns financing/infrastructure for Chinese study abroad through a British loan, but not U.S.-educated Chinese specifically."
}
```
