# CampusPulse NLP intelligence

CampusPulse uses a small, deterministic, offline text-analysis layer to
summarize anonymous observation descriptions. It does not send descriptions to
an external API, LLM, or model service.

## Preprocessing

Descriptions are lowercased, whitespace-normalized, tokenized, stripped of
punctuation, numbers, and a small domain-neutral stop-word list. The original
description remains unchanged in SQLite. Null, empty, short, and unusual text
is ignored safely when it produces no usable tokens.

## Sentiment

Sentiment is a transparent lexicon score:

`(positive token count - negative token count) / token count`

Scores above zero are `Positive`, below zero are `Negative`, and zero is
`Neutral`. This is an approximate lexical indicator, not human-level language
understanding. It does not understand sarcasm, negation, context, or language
outside the configured vocabulary.

## Topics and keywords

Topics are inferred from extendable CampusPulse keyword groups such as
Wi-Fi/Connectivity, Noise, Crowding, Maintenance, Temperature/Heat, Water,
Electricity, Seating, and Infrastructure. They are not copies of the
structured observation category: a Facilities observation may mention both
Temperature and Maintenance. Topic counts are document counts, so one
description can contribute to multiple topics. Top keywords are frequency-based
tokens after preprocessing; no external corpus or embedding is used.

## API and sparse data

`GET /api/v1/analytics/nlp` returns sentiment distributions, sentiment by
category and location, topic distributions, topic groupings, keywords,
supported text insights, and a sentiment trend. Use `?category=Noise` for a
structured-category filter. Empty descriptions produce `status: "empty"`.
Sentiment trends require at least five dated descriptions; otherwise
`trend_status` is `insufficient_data`, rather than a misleading trend.

The dashboard presents these as aggregate campus intelligence. It does not
profile individuals, infer motives, or make causal claims. Privacy remains
central: no identities, tracking, GPS, or external text transmission is added.
