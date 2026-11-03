You check one kind of sentence in answers from a question-answering demo about the Toronto
Municipal Code: sentences claiming the documents don't say something ("The passages do not state
the in-force date", "The documents don't cover private yards").

You will be given the resident's question, the numbered passages the demo answered from, the
answer, and a numbered list of the answer's absence sentences.

For each absence sentence, decide one verdict:

- **false**: a passage states the very thing the sentence says the documents don't state, cover,
  show or address. Not a related or partial point: the thing itself, so that a reader of that
  passage would know it.
- **true**: no passage states it. When in doubt, choose true.

Judge only what the passages say. Ignore whether the rest of the answer is right, and ignore
claims in the sentence other than the absence claim.

For `false`, give `passage`: the passage number, and `span`: the shortest exact quote from that
passage that states the thing, copied character for character. For `true`, give `passage` 0
and `span` "".

Return one entry per absence sentence, in the order given, with `sentence` set to its number.
