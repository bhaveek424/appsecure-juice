import { describe, expect, it } from "vitest";
import {
  isFailedReviewRun,
  reviewRunPanelTitle,
  shouldShowActiveRunBanner,
} from "./reviewRunView";

describe("reviewRunView", () => {
  it("detects failed Review Runs", () => {
    expect(isFailedReviewRun("Failed")).toBe(true);
    expect(isFailedReviewRun("Ready For Skills")).toBe(false);
  });

  it("labels the panel for cancelled and active runs", () => {
    expect(reviewRunPanelTitle("Cancelled")).toBe("Cancelled Review Run");
    expect(reviewRunPanelTitle("Zapping")).toBe("Active Review Run");
    expect(reviewRunPanelTitle("Completed")).toBe("Review Run");
  });

  it("shows active-run banner when viewing history while another run is active", () => {
    expect(
      shouldShowActiveRunBanner({
        selectedRunId: "history-1",
        activeRunId: "active-1",
      }),
    ).toBe(true);
    expect(
      shouldShowActiveRunBanner({
        selectedRunId: "active-1",
        activeRunId: "active-1",
      }),
    ).toBe(false);
  });
});
