import katex from "katex";

export function Formula({ tex, caption }: { tex: string; caption: string }) {
  let html = "";
  let failed = false;
  try {
    html = katex.renderToString(tex, { displayMode: true, throwOnError: true });
  } catch {
    failed = true;
  }
  return (
    <figure className="formula">
      {failed ? (
        <p className="note">This equation could not be rendered.</p>
      ) : (
        <div className="formula-body" dangerouslySetInnerHTML={{ __html: html }} />
      )}
      <figcaption>{caption}</figcaption>
    </figure>
  );
}
