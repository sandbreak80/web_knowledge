import { notFound } from "next/navigation";

interface OutputPageProps {
  params: { id: string };
}

export default function OutputPage({ params }: OutputPageProps) {
  const { id } = params;

  if (!id) {
    notFound();
  }

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">
          Output Browser · {id}
        </h1>
        <p className="text-sm text-muted-foreground">
          Explore the generated Markdown, manifest, and graph artifacts. This
          page will host the split layout (tree + file preview) powered by
          `OutputTree`, `OutputFileList`, and `MarkdownPreview` components.
        </p>
      </header>
      <div className="rounded-xl border border-dashed border-slate-300 p-6 text-sm text-muted-foreground dark:border-slate-700">
        <p>
          TODO: Build a two-column layout with lazy directory fetching and
          Markdown preview. Include download buttons and copy-to-clipboard.
        </p>
      </div>
    </div>
  );
}
