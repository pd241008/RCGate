import { useState } from "react";

import { formatPercent } from "../fusion";
import { verifyWorked } from "../math";
import { CHECKS, SOURCE_QUALITY_NOTE } from "../signals";
import type { ScoreResult } from "../studioTypes";
import { Formula } from "./Formula";

export function ScorePanel({ score, pending }: { score: ScoreResult | null; pending: string | null }) {
  const [open, setOpen] = useState(false);
  if (!score && pending) {
    return (
      <article className="stage" id="stage-result">
        <p className="stage-kicker">RC-Gate result</p>
        <h2>Scoring this sentence</h2>
        <p className="pending" role="status">
          {pending}
        </p>
        <p className="note">This wait is local computation or a checkpoint load. It is not a live provider writing an answer.</p>
      </article>
    );
  }
  if (!score || score.status !== "complete" || !score.prediction || !score.claim) {
    return (
      <article className="stage" id="stage-result">
        <p className="stage-kicker">RC-Gate result</p>
        <h2>This sentence was not scored</h2>
        <p>{score?.reason ?? pending ?? "No score is available."}</p>
      </article>
    );
  }

  const { prediction, claim } = score;
  const crossShare = Math.max(prediction.w_cross, 0);
  const evidShare = Math.max(prediction.w_evid, 0);
  const total = crossShare + evidShare || 1;
  const worked = verifyWorked(score);
  const featureNote = featureCopy(score.feature_source);

  return (
    <article className="stage" id="stage-result">
      <p className="stage-kicker">RC-Gate result</p>
      <h2>What was scored?</h2>
      <p className="highlight">{claim.claim_text}</p>
      <p>
        This sentence is from the stored {claim.model_name} answer. The probability belongs only to this sentence, not to the rest of that answer.
      </p>
      {claim.dealias_changed && (
        <p className="note">
          The scoring input rewrote a pronoun in the stored sentence. The highlighted answer text above the score is the original sentence.
        </p>
      )}

      <h2>What is the prediction?</h2>
      <p className="result-prob">{formatPercent(prediction.prob)}</p>
      <p className="note">Estimated hallucination probability. Stored value {prediction.prob.toFixed(4)}.</p>
      <p className="class-line">
        {prediction.predicted_class}, using a threshold of {prediction.threshold.toFixed(1)}. This is a model prediction, not ground truth, and it does not prove the sentence true or false.
      </p>
      {prediction.close_note && <p className="caution">{prediction.close_note}</p>}
      <p className="note">This probability is a demo inference. It is not a benchmark score for the question.</p>
      {featureNote && <p className="note">{featureNote}</p>}

      <h2>What did the checks observe?</h2>
      <ul className="signal-list">
        {CHECKS.map((check) => {
          const value = prediction.signals[check.key];
          return (
            <li key={check.key}>
              <div className="signal-head">
                <span>{check.label}</span>
                <span>{value.toFixed(4)}</span>
              </div>
              <div className="signal-track" aria-hidden="true">
                <span style={{ width: `${Math.max(0, Math.min(1, value)) * 100}%` }} />
              </div>
              <p>{check.plain}</p>
              <p className="note">{check.high}</p>
              <p className="note">{check.low}</p>
              <p className="note">{check.cannot}</p>
            </li>
          );
        })}
      </ul>
      <p className="note">
        The extractor checked {prediction.evidence_n_passages} sentences from the supplied context ({prediction.evidence_source}) and compared this sentence with {prediction.cross_n_others} other recorded answers. Arithmetic verdict: {prediction.arithmetic_verdict}.
      </p>

      <h2>How did the gate combine the checks?</h2>
      <p>
        RC-Gate has two linear scoring experts. One reads the cross-model comparisons. The other reads the supplied evidence. The gate sees the claim type ({claim.claim_type_name}) and the generator, not the signal values. Its two routing weights scale the expert scores. A final linear step and a sigmoid turn that pair into the probability above.
      </p>
      <div className="route-labels">
        <span>Cross-model weight {prediction.w_cross.toFixed(4)}</span>
        <span>Evidence weight {prediction.w_evid.toFixed(4)}</span>
      </div>
      <div
        className="route"
        role="img"
        aria-label={`Routing weights. Cross-model ${prediction.w_cross.toFixed(4)}, evidence ${prediction.w_evid.toFixed(4)}.`}
      >
        <span className="route-cross" style={{ width: `${(crossShare / total) * 100}%` }} />
        <span className="route-evid" style={{ width: `${(evidShare / total) * 100}%` }} />
      </div>
      <p className="note">These weights are not proof that one family is more reliable.</p>
      <dl className="logit-grid">
        <div>
          <dt>Cross-model expert logit</dt>
          <dd>{prediction.z_cross.toFixed(4)}</dd>
        </div>
        <div>
          <dt>Evidence expert logit</dt>
          <dd>{prediction.z_evid.toFixed(4)}</dd>
        </div>
        <div>
          <dt>Final logit</dt>
          <dd>{prediction.logit.toFixed(4)}</dd>
        </div>
        <div>
          <dt>Probability</dt>
          <dd>{prediction.prob.toFixed(4)}</dd>
        </div>
      </dl>

      <div className="result-actions">
        <button className="pill" type="button" aria-expanded={open} onClick={() => setOpen((value) => !value)}>
          How did RC-Gate score this?
        </button>
      </div>
      {open && score.experts && (
        <section className="math-panel">
          <h3>The mathematics</h3>
          <Formula
            tex="z_{\text{cross}} = a_{\text{cross}}^{\top} s_{\text{cross}} + b_{\text{cross}}"
            caption="The cross-model expert is a weighted sum of agreement, contradiction, and semantic difference, plus a bias."
          />
          <p className="worked">
            With this sentence, that sum is {worked ? worked.zCross.toFixed(4) : prediction.z_cross.toFixed(4)}. The checkpoint reported {prediction.z_cross.toFixed(4)}.
          </p>
          <Formula
            tex="z_{\text{evidence}} = a_{\text{evidence}}^{\top} s_{\text{evidence}} + b_{\text{evidence}}"
            caption="The evidence expert is a weighted sum of support, source quality, and conflict, plus a bias."
          />
          <p className="worked">
            With this sentence, that sum is {worked ? worked.zEvid.toFixed(4) : prediction.z_evid.toFixed(4)}. The checkpoint reported {prediction.z_evid.toFixed(4)}.
          </p>
          <Formula
            tex="w = \operatorname{softmax}(g(x_{\text{meta}}))"
            caption="The routing weights are the checkpoint’s softmax output for this claim type and generator. The browser does not re-run the gate network."
          />
          <p className="worked">
            w_cross = {prediction.w_cross.toFixed(4)}, w_evidence = {prediction.w_evid.toFixed(4)}.
          </p>
          <Formula
            tex="\ell = \phi^{\top}\begin{bmatrix} w_{\text{cross}} z_{\text{cross}} \\ w_{\text{evidence}} z_{\text{evidence}} \end{bmatrix} + b_{\phi}"
            caption="The fusion step takes the two weighted expert logits, applies one more linear step, and produces the final logit."
          />
          <p className="worked">
            The recomputed logit is {worked ? worked.logit.toFixed(4) : prediction.logit.toFixed(4)}. The checkpoint reported {prediction.logit.toFixed(4)}.
          </p>
          <Formula
            tex="P(\text{hallucinated}) = \sigma(\ell) = \frac{1}{1+e^{-\ell}}"
            caption="The sigmoid turns that logit into a probability between 0 and 1."
          />
          <p className="worked">
            {worked?.matchesModel && score.worked?.matches_model
              ? "The worked calculation matches the model output within rounding tolerance."
              : "The worked calculation does not match the model output. The probability above is still the checkpoint’s output."}
          </p>
          <details>
            <summary>Technical signal: source quality</summary>
            <p>
              src_quality = {prediction.signals.src_quality.toFixed(4)}. {SOURCE_QUALITY_NOTE}
            </p>
          </details>
        </section>
      )}

      <details className="run-details">
        <summary>Run details</summary>
        <dl>
          <div>
            <dt>Source ID</dt>
            <dd>{claim.source_id}</dd>
          </div>
          <div>
            <dt>Response ID</dt>
            <dd>{claim.response_id}</dd>
          </div>
          <div>
            <dt>Claim ID</dt>
            <dd>{claim.claim_id}</dd>
          </div>
          <div>
            <dt>Feature source</dt>
            <dd>{score.feature_source}</dd>
          </div>
          <div>
            <dt>Checkpoint</dt>
            <dd>{score.checkpoint ? `${score.checkpoint.path} (${score.checkpoint.variant}, split ${score.checkpoint.split_seed}, model ${score.checkpoint.model_seed})` : "none"}</dd>
          </div>
          <div>
            <dt>Cache</dt>
            <dd>{score.cache_path ?? "not used"}</dd>
          </div>
          <div>
            <dt>Dataset span label</dt>
            <dd>
              {claim.human_span_label === 1
                ? "The RAGTruth span annotation overlaps this sentence. That label is not the probability above."
                : "The RAGTruth span annotation does not overlap this sentence. That label is not the probability above."}
            </dd>
          </div>
        </dl>
        {score.partition_note && <p>{score.partition_note}</p>}
        {score.notes.map((note) => (
          <p key={note} className="note">
            {note}
          </p>
        ))}
        {score.benchmark_evaluation && <p>Benchmark flag was set, which this studio should not do.</p>}
      </details>
    </article>
  );
}

function featureCopy(source: string | null): string | null {
  if (source === "precomputed_row") {
    return "Features came from a stored signal-table row. The checkpoint was loaded. Nothing was trained.";
  }
  if (source === "local_extraction") {
    return "Signals were calculated on this machine from the stored texts. This is actual local computation, not a simulated live provider response.";
  }
  if (source === "cached_local_extraction") {
    return "Signals were loaded from a local demo cache of an earlier calculation on this machine.";
  }
  return null;
}
