-- Does a rough anonymization of an Input database. Note that this does
-- not necessarily clear out all confidential information and should
-- not be considered approval to distribute this Input database publicly.
-- Talk to willkg if you have questions.

TRUNCATE django_session;

UPDATE feedback_responseemail SET
       email = 'foo@example.com';
