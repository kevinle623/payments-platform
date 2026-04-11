import Link from "next/link";
import { FileQuestion } from "lucide-react";
import { PageHeader } from "@/components/common/page-header";

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-[60vh] w-full max-w-3xl flex-col items-center justify-center px-4">
      <div className="w-full rounded-2xl border border-border bg-card p-8 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-border bg-background">
          <FileQuestion className="h-6 w-6 text-foreground-subtle" />
        </div>

        <PageHeader
          title="Page Not Found"
          description="The page you requested does not exist or may have been moved."
          className="mx-auto max-w-xl items-center justify-center border-none pb-0 text-center sm:flex-col sm:items-center sm:justify-center"
        />

        <p className="mt-3 text-xs font-medium uppercase tracking-[0.2em] text-foreground-subtle">
          404
        </p>

        <div className="mt-6">
          <Link
            href="/"
            className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary-hover"
          >
            Back To Overview
          </Link>
        </div>
      </div>
    </div>
  );
}
