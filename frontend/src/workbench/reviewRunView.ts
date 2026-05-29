import { isActiveReviewRun, isCancelledReviewRun } from "../api";

export function isFailedReviewRun(status: string): boolean {
  return status === "Failed";
}

export function reviewRunPanelTitle(status: string): string {
  if (isCancelledReviewRun(status)) {
    return "Cancelled Review Run";
  }
  if (isFailedReviewRun(status)) {
    return "Failed Review Run";
  }
  if (isActiveReviewRun(status)) {
    return "Active Review Run";
  }
  return "Review Run";
}

export function shouldShowActiveRunBanner(options: {
  selectedRunId: string | null;
  activeRunId: string | undefined;
}): boolean {
  const { selectedRunId, activeRunId } = options;
  return (
    activeRunId !== undefined &&
    selectedRunId !== null &&
    selectedRunId !== activeRunId
  );
}
