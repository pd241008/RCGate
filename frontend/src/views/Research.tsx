import reportUrl from "../../../docs/RC-Gate_Final_Research_Report_v1.md?url";
import indexUrl from "../../../docs/RC-Gate_Experiment_Index.md?url";

import { BASELINES, RESEARCH_FIGURES } from "../researchFigures";

export function Research() {
  const figures = RESEARCH_FIGURES;
  return (
    <article className="prose guide">
      <p className="kicker">Research</p>
      <h1>What the repeated fits actually say</h1>
      <p>
        The numbers below are the Stage 8 means from the final research report. They describe {figures.nGroupSplits} question-grouped splits crossed with {figures.nModelInitialisations} model initialisations on one corrected {figures.nSentences}-sentence RAGTruth slice ({figures.nQuestions} questions, {figures.nHallucinated} hallucinated sentences). That is 60 fits of each model on one pool. They are not 60 independent datasets, and a probability in the library is not one of these benchmark scores.
      </p>
      <table className="research-table">
        <caption>Mean test AUROC on the corrected 800-sentence slice.</caption>
        <thead>
          <tr>
            <th scope="col">Model</th>
            <th scope="col">What it is</th>
            <th scope="col">Mean test AUROC</th>
          </tr>
        </thead>
        <tbody>
          {BASELINES.map((row) => (
            <tr key={row.id}>
              <th scope="row">{row.id}</th>
              <td>{row.name}</td>
              <td>{row.figure}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p>
        Mean paired A7 − A4: {figures.meanA7MinusA4}. Mean paired A7 − A0: {figures.meanA7MinusA0}. A7’s 60 AUROC values have sample standard deviation {figures.a7SampleSd}. That spread describes repeated fits on one question pool. It is not a confidence interval.
      </p>

      <section>
        <h2>The benchmark and its limits</h2>
        <p>
          The slice is question-grouped, so all of a source’s scored sentences stay on the same side of a split. The official RAGTruth train/test field is not the split used here. Test folds are small, and moving the 134 questions changes the rank metrics. The result is about this slice, not about hallucination detection in general.
        </p>
      </section>

      <section>
        <h2>The sentence-level annotation rule</h2>
        <p>
          RAGTruth marks character spans, not whole sentences. This repository labels a sentence as hallucinated when it overlaps any span of Evident Conflict, Subtle Conflict, Evident Baseless Info, or Subtle Baseless Info. A sentence that only partly overlaps a marked span still counts. The studio shows that dataset label in Run details, separate from the model probability.
        </p>
      </section>

      <section>
        <h2>The synthetic test is a mechanism check</h2>
        <p>
          On synthetic tables, a reliability pattern was written into the generator. The gate can recover that planted pattern. Recovery shows the mechanism can respond when the pattern is put there by construction. It is not evidence about real generators. On the synthetic pooled mean, A4 still ranks above A7.
        </p>
      </section>

      <section>
        <h2>A7 did not establish an advantage on this slice</h2>
        <p>
          The comparison that matters is A7, the full metadata-conditioned gate, against A4, gradient boosting with the same six signals plus claim type and generator identity, without the gate constraint. The mean paired difference A7 minus A4 is {figures.meanA7MinusA4}. A7 also sits below A0, the logistic regression on the six signals alone. The real-data result does not show that the gate ranks hallucinated sentences better than those flat models.
        </p>
      </section>

      <section>
        <h2>A constant source-quality signal and an inactive arithmetic checker</h2>
        <p>
          Source quality is 0.9 on every row of the evaluated slice, because the evidence is the benchmark context. It cannot change a ranking. The arithmetic checker looks for an explicit expression and otherwise returns unverifiable. On the corrected 800-row slice it is unverifiable on every row, including the numeric claims. Five other signals do vary. These two paths do not.
        </p>
      </section>

      <section>
        <h2>The official QA release does not identify the reliability surface</h2>
        <p>
          A read-only audit applied a pre-specified support rule: at least 30 training positives and 15 official-test positives in a generator-by-type cell. Under that rule the official QA data do not adequately identify the proposed generator-by-type reliability surface. No full-scale feature build or model fit was performed for that audit.
        </p>
      </section>

      <section>
        <h2>A8 judge voting was not evaluated</h2>
        <p>
          A8 would have been a majority vote over judge models. The signal tables have no judge-vote columns, so A8 was never fit. The voting clause of the original hypothesis is untested, not failed.
        </p>
      </section>

      <div className="doc-links">
        <a href={reportUrl}>Final research report</a>
        <a href={indexUrl}>Experiment index</a>
      </div>
      <p className="note">
        Repository paths: {figures.reportPath} and {figures.indexPath}.
      </p>
    </article>
  );
}
