import { CANDIDATES, CONTEXT_PASSAGES } from "@/lib/ask/config";
import { EVALS } from "./evals/data";

/** The sources panel before a question (UI.md, "Before a question"): the pipeline the answer goes through. */
export function HowItWorks() {
  return (
    <div className="how">
      <h2>How an answer is made</h2>
      <ol>
        <li>
          <strong>Search.</strong> Finds the {CANDIDATES} passages closest to your question, by wording and by meaning.
        </li>
        <li>
          <strong>Rerank.</strong> Keeps the best {CONTEXT_PASSAGES} and scores how well each one matches.
        </li>
        <li>
          <strong>Stop if nothing fits.</strong> When no passage scores high enough, it says the documents don&apos;t
          cover this. No answer is written.
        </li>
        <li>
          <strong>Answer.</strong> A model writes from those passages only and numbers the passage behind each claim.
        </li>
        <li>
          <strong>Check.</strong> Every number is checked against the passages. An answer it can&apos;t back is
          withheld.
        </li>
      </ol>
      <p className="how-foot">
        The cited passages open here, each linked to the City&apos;s own PDF or agenda item.
        {EVALS.intro && (
          <>
            {" "}
            Tested on {EVALS.intro.questions} questions, {EVALS.intro.refuse} of them meant to be refused:{" "}
            <a href="/evals">see the evals</a>.
          </>
        )}
      </p>
    </div>
  );
}
