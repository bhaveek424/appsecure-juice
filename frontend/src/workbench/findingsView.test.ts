import { describe, expect, it } from "vitest";
import type { Finding } from "../api";
import {
  filterFindings,
  sortFindings,
  type FindingFilters,
} from "./findingsView";

const sampleFindings: Finding[] = [
  {
    id: "1",
    source: "Scanner",
    title: "XSS",
    category: "Injection",
    severity: "High",
    endpoint: "/search",
    description: "",
    remediation: "",
    confidence: null,
    evidence_excerpt: null,
    discovered_at: "2026-01-01T00:00:00Z",
    disposition: "Unreviewed",
  },
  {
    id: "2",
    source: "Business Logic",
    title: "Basket leak",
    category: "Account Boundary",
    severity: "Critical",
    endpoint: "/basket",
    description: "",
    remediation: "",
    confidence: null,
    evidence_excerpt: null,
    discovered_at: "2026-01-01T00:00:00Z",
    disposition: "True Positive",
  },
  {
    id: "3",
    source: "Scanner",
    title: "Info leak",
    category: "Info",
    severity: "Low",
    endpoint: "/api",
    description: "",
    remediation: "",
    confidence: null,
    evidence_excerpt: null,
    discovered_at: "2026-01-01T00:00:00Z",
    disposition: "False Positive",
  },
];

const allFilters: FindingFilters = {
  source: "all",
  severity: "all",
  disposition: "all",
};

describe("filterFindings", () => {
  it("returns all findings when filters are all", () => {
    expect(filterFindings(sampleFindings, allFilters)).toHaveLength(3);
  });

  it("filters by source", () => {
    const filtered = filterFindings(sampleFindings, {
      ...allFilters,
      source: "Scanner",
    });
    expect(filtered.map((finding) => finding.id)).toEqual(["1", "3"]);
  });

  it("filters by severity", () => {
    const filtered = filterFindings(sampleFindings, {
      ...allFilters,
      severity: "Critical",
    });
    expect(filtered.map((finding) => finding.id)).toEqual(["2"]);
  });

  it("filters by Review Disposition", () => {
    const filtered = filterFindings(sampleFindings, {
      ...allFilters,
      disposition: "True Positive",
    });
    expect(filtered.map((finding) => finding.id)).toEqual(["2"]);
  });
});

describe("sortFindings", () => {
  it("sorts by severity with Critical first", () => {
    const sorted = sortFindings(sampleFindings, "severity");
    expect(sorted.map((finding) => finding.severity)).toEqual([
      "Critical",
      "High",
      "Low",
    ]);
  });
});
