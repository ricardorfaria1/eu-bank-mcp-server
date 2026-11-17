# Compliance notes

[Português](COMPLIANCE.pt.md)

How the server's design relates to three EU regulations. This is a portfolio project on synthetic data, not legal advice and not a compliance assessment.

## GDPR (Regulation (EU) 2016/679)

| Article | Requirement | In this server |
|---|---|---|
| 5(1)(c) | Data minimisation | Each role receives only the fields it needs (see the table in the README). NIF and IBAN are always masked; the analyst gets age instead of birth date and country instead of address. |
| 25 | Data protection by design and by default | Restrictions live in the server, not in the prompt. Tools a role may not use are not registered, so the model does not know they exist. The database is opened read-only. |
| 15 | Right of access | The audit log records when each customer's data was consulted, for what kind of lookup, and which fields. It supports the controller's answer (dates, purposes, categories of data). The CJEU held in C-579/21 (Pankki S, 2023) that article 15 does not, in principle, require naming the employees who consulted the data. |
| 30 | Records of processing | The audit log is an input to the record of processing, not a substitute for it. |
| 5(2), 32 | Accountability, security of processing | Logging every access helps demonstrate compliance and detect misuse. |

The audit log never stores field values or search terms. It would otherwise become a second copy of the personal data it is meant to protect.

## Anti-money laundering (Regulation (EU) 2024/1624, AMLR)

Article 73 forbids obliged entities and their staff from telling a customer, or anyone else, that information about them is being analysed or reported as suspicious ("tipping off"). The AMLR applies from 10 July 2027; until then the same prohibition comes from national law transposing Directive (EU) 2015/849.

In this server:

- AML alerts exist in the database and no tool returns them, for any role. Alerts belong to the compliance team's own systems, and keeping them away from customer-facing staff and from the model removes one way of tipping off by accident.
- PEP status and KYC status are not suspicion, so tipping-off does not apply to them. Attendants still do not receive them, on data minimisation grounds (GDPR article 5(1)(c)): answering a customer about limits or service history does not need them.
- Search is limited (complete NIF or 3+ letters of the name, at most 5 results, at most 20 customers per session), so the model cannot be used to sweep the base.

## AI Act (Regulation (EU) 2024/1689)

Annex III, point 5(b), classifies as high-risk the AI systems intended to evaluate the creditworthiness of natural persons or establish their credit score, except systems used to detect financial fraud.

This server retrieves data and makes no decision. It does not score anyone; the credit score it returns comes from the bank's existing systems, and a person decides. On its own it is a data access component.

If it were wired into a system that assesses creditworthiness, that system would be high-risk and the server would be part of it. The design already supports two of the obligations that would follow:

- Record-keeping (Article 12): every tool call is logged with operator, role, customers and fields.
- A person decides: the model only retrieves and summarises, and no tool approves, rejects or changes anything. This makes human oversight possible but is not, on its own, the set of oversight measures Article 14 requires of the provider.

It would still lack, among others: a risk management system (Article 9), data governance of the scoring model (Article 10), technical documentation (Article 11), accuracy and robustness testing of the model itself (Article 15), and conformity assessment.

According to the secondary sources listed below, Regulation (EU) 2026/1744 (the "Digital Omnibus on AI") moved the date from which Annex III high-risk obligations apply from 2 August 2026 to 2 December 2027. This has not been checked against the Official Journal; do that before relying on the date.

## Not covered

Authentication (the role comes from the server configuration), encryption at rest, a retention period for the audit log, and a data protection impact assessment. A production version would need all of them.

## Sources

- GDPR: <https://eur-lex.europa.eu/eli/reg/2016/679/oj>
- AMLR: <https://eur-lex.europa.eu/eli/reg/2024/1624/oj>, article 73 also at <https://www.springlex.eu/en/packages/aml/amlr-regulation/article-73/>
- AI Act: <https://eur-lex.europa.eu/eli/reg/2024/1689/oj>
- Digital Omnibus on AI: <https://www.regulation-ai.eu/en/omnibus/>, <https://cdp.cooley.com/digital-ai-omnibus-delays-key-deadlines-introduces-new-rules/>
