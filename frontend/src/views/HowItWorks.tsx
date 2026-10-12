export function HowItWorks() {
  return (
    <article className="prose guide">
      <p className="kicker">How RC-Gate works</p>
      <h1>A sentence checker, explained from the start</h1>
      <p>
        RC-Gate estimates whether one sentence in a stored answer is hallucinated. In this project, that means the sentence overlaps a passage a human annotator marked as conflicting with the supplied material, or as not supported by it. The estimate is a probability. It is not proof, and it is not a live call to the model that wrote the answer.
      </p>
      <ol className="pipeline" aria-label="RC-Gate pipeline">
        <li>
          <strong>Task</strong>
          <span>A question, a summary job, or a data-to-text job, stored with its source material.</span>
        </li>
        <li>
          <strong>Answers</strong>
          <span>Six recorded models answered that same source. Their texts are already saved.</span>
        </li>
        <li>
          <strong>One sentence</strong>
          <span>The checker scores a single sentence, not the whole answer.</span>
        </li>
        <li>
          <strong>Two checks</strong>
          <span>One compares the other models. One reads the material that came with the task.</span>
        </li>
        <li>
          <strong>Gate</strong>
          <span>A small router, seeing only claim type and writer, mixes the two checks into a probability.</span>
        </li>
      </ol>

      <section>
        <h2>Why a fluent sentence can still be unsupported</h2>
        <p>
          A sentence can sound specific and still go beyond the material the model was given. It can invent a number, name the wrong person, or smooth over a gap. Reading it once is not enough, because fluent writing is not the same thing as support from the source.
        </p>
      </section>

      <section>
        <h2>Why the models disagree</h2>
        <p>
          The local dataset stores six answers to each source: GPT-4-0613, GPT-3.5-turbo-0613, Mistral-7B-Instruct, and three Llama-2 chat models. They often choose different details. RC-Gate treats that disagreement as a clue. If the other answers entail the sentence, agreement is high. If one of them flatly conflicts, the contradiction signal keeps that strongest clash. If the wording sits far from the others, the difference signal rises.
        </p>
        <details>
          <summary>How agreement and contradiction are measured</summary>
          <p>
            Agreement is the fraction of the other answers whose text entails the sentence. Contradiction is the single largest contradiction score among those answers, not an average. Semantic difference is one minus the average similarity between the sentence and each other answer’s closest sentence. None of these three, by itself, proves the sentence true or false.
          </p>
        </details>
      </section>

      <section>
        <h2>What the supplied passages are, and what they are not</h2>
        <p>
          The original models saw the passages, article, or business record stored with the task. RC-Gate’s evidence signals read that same material. They ask whether it supports the sentence and whether it conflicts with the sentence. This is not a second search of the web after the answer was written. An independent reference, when this studio has one, is a separate page for you to read. It is not fed into the score.
        </p>
        <details>
          <summary>How support and conflict are measured</summary>
          <p>
            The extractor picks a few sentences from the supplied context and scores entailment and contradiction against the claim. Support is the strongest entailment. Conflict is the strongest contradiction. A constant called source quality records that the evidence came from the task context. On the evaluated slice that constant does not vary, so it does not rank one example against another.
          </p>
        </details>
      </section>

      <section>
        <h2>Claim type and who wrote the sentence</h2>
        <p>
          Rules label the sentence as numeric, entity, extractive, or abstractive. The gate also sees which of the six models wrote it. Those two facts are all the gate is allowed to see. It does not see the six signal numbers. The idea was that some writers, or some kinds of sentence, might make one family of checks more useful than the other. On the evaluated data, that idea was not established.
        </p>
      </section>

      <section>
        <h2>Experts, the gate, logits, and the sigmoid</h2>
        <p>
          Each expert is a weighted sum. The cross-model expert reads agreement, contradiction, and difference. The evidence expert reads support, source quality, and conflict. Each sum is a logit: a score that can be negative or positive. The gate’s two weights, which add up to one, scale those logits. One more weighted sum produces a final logit. The sigmoid squashes that logit into a probability between 0 and 1. A logit of zero becomes 50%.
        </p>
        <p>
          You can open the mathematics on a scored sentence and see the same steps with that sentence’s numbers. The routing weights are visible. They are not a validated explanation of which check is trustworthy.
        </p>
      </section>

      <section>
        <h2>A probability is not a proof</h2>
        <p>
          The percentage is the model’s estimate that the sentence is hallucinated under the definition above. It is not ground truth. Near 50%, the estimate sits close to the classification threshold and should be read cautiously. The studio does not add a second confidence number on top of that probability.
        </p>
      </section>

      <section>
        <h2>This is not a live multi-provider product</h2>
        <p>
          The answers were recorded in RAGTruth. The studio does not ask GPT, Claude, or any other provider to write a new answer, and it does not search the web while you read. Some sentences already have features in a saved table. Others can be scored on this machine with the local checker weights and one saved checkpoint. If those weights are missing, the record still opens and the score is left blank.
        </p>
      </section>
    </article>
  );
}
