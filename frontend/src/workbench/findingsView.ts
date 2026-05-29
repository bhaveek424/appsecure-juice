import type { Finding, ReviewDisposition } from "../api";
import { SEVERITY_ORDER } from "../api";

export type FindingSortKey = "severity" | "title" | "endpoint";

export type FindingFilters = {
  source: string;
  severity: string;
  disposition: ReviewDisposition | "all";
};

export const DEFAULT_FINDING_FILTERS: FindingFilters = {
  source: "all",
  severity: "all",
  disposition: "all",
};

export function filterFindings(
  findings: Finding[],
  filters: FindingFilters,
): Finding[] {
  return findings.filter((finding) => {
    if (filters.source !== "all" && finding.source !== filters.source) {
      return false;
    }
    if (filters.severity !== "all" && finding.severity !== filters.severity) {
      return false;
    }
    if (
      filters.disposition !== "all" &&
      finding.disposition !== filters.disposition
    ) {
      return false;
    }
    return true;
  });
}

export function sortFindings(
  findings: Finding[],
  sortKey: FindingSortKey,
): Finding[] {
  const items = [...findings];
  items.sort((left, right) => {
    if (sortKey === "severity") {
      const rank =
        (SEVERITY_ORDER[left.severity] ?? 99) -
        (SEVERITY_ORDER[right.severity] ?? 99);
      if (rank !== 0) {
        return rank;
      }
    }
    if (sortKey === "endpoint") {
      return left.endpoint.localeCompare(right.endpoint);
    }
    return left.title.localeCompare(right.title);
  });
  return items;
}

export function uniqueFindingSources(findings: Finding[]): string[] {
  return [...new Set(findings.map((finding) => finding.source))].sort();
}

export function uniqueFindingSeverities(findings: Finding[]): string[] {
  const severities = [...new Set(findings.map((finding) => finding.severity))];
  severities.sort(
    (left, right) =>
      (SEVERITY_ORDER[left] ?? 99) - (SEVERITY_ORDER[right] ?? 99),
  );
  return severities;
}
