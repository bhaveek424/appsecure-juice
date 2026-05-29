import { useMemo, useState } from "react";
import type { Finding, FindingCounts, ReviewDisposition } from "./api";
import { REVIEW_DISPOSITIONS } from "./api";
import { EmptyState } from "./components/WorkbenchState";
import {
  DEFAULT_FINDING_FILTERS,
  filterFindings,
  sortFindings,
  uniqueFindingSeverities,
  uniqueFindingSources,
  type FindingFilters,
  type FindingSortKey,
} from "./workbench/findingsView";

type Props = {
  findings: Finding[];
  findingCounts?: FindingCounts;
  onSelectFinding?: (findingId: string) => void;
};

export default function FindingsList({
  findings,
  findingCounts,
  onSelectFinding,
}: Props) {
  const [sortKey, setSortKey] = useState<FindingSortKey>("severity");
  const [filters, setFilters] = useState<FindingFilters>(DEFAULT_FINDING_FILTERS);

  const sources = useMemo(() => uniqueFindingSources(findings), [findings]);
  const severities = useMemo(
    () => uniqueFindingSeverities(findings),
    [findings],
  );

  const visibleFindings = useMemo(() => {
    const filtered = filterFindings(findings, filters);
    return sortFindings(filtered, sortKey);
  }, [findings, filters, sortKey]);

  if (findings.length === 0) {
    return (
      <EmptyState
        title="No Findings yet"
        description="Scanner Findings appear after ZAP completes. Business Logic Findings appear when a Review Skill records evidence."
      />
    );
  }

  return (
    <div className="findings">
      <h4>Findings</h4>
      {findingCounts && (
        <div className="severity-counts">
          <span className="severity-pill critical">
            Critical {findingCounts.critical}
          </span>
          <span className="severity-pill high">High {findingCounts.high}</span>
          <span className="severity-pill medium">
            Medium {findingCounts.medium}
          </span>
          <span className="severity-pill low">Low {findingCounts.low}</span>
          <span className="severity-pill informational">
            Info {findingCounts.informational}
          </span>
        </div>
      )}

      <div className="findings-toolbar">
        <label htmlFor="finding-sort">Sort Findings by</label>
        <select
          id="finding-sort"
          value={sortKey}
          onChange={(event) => setSortKey(event.target.value as FindingSortKey)}
        >
          <option value="severity">Severity</option>
          <option value="title">Title</option>
          <option value="endpoint">Endpoint</option>
        </select>

        <label htmlFor="finding-source-filter">Source</label>
        <select
          id="finding-source-filter"
          value={filters.source}
          onChange={(event) =>
            setFilters((current) => ({ ...current, source: event.target.value }))
          }
        >
          <option value="all">All sources</option>
          {sources.map((source) => (
            <option key={source} value={source}>
              {source}
            </option>
          ))}
        </select>

        <label htmlFor="finding-severity-filter">Severity</label>
        <select
          id="finding-severity-filter"
          value={filters.severity}
          onChange={(event) =>
            setFilters((current) => ({
              ...current,
              severity: event.target.value,
            }))
          }
        >
          <option value="all">All severities</option>
          {severities.map((severity) => (
            <option key={severity} value={severity}>
              {severity}
            </option>
          ))}
        </select>

        <label htmlFor="finding-disposition-filter">Review Disposition</label>
        <select
          id="finding-disposition-filter"
          value={filters.disposition}
          onChange={(event) =>
            setFilters((current) => ({
              ...current,
              disposition: event.target.value as ReviewDisposition | "all",
            }))
          }
        >
          <option value="all">All dispositions</option>
          {REVIEW_DISPOSITIONS.map((disposition) => (
            <option key={disposition} value={disposition}>
              {disposition}
            </option>
          ))}
        </select>
      </div>

      {visibleFindings.length === 0 ? (
        <EmptyState
          title="No Findings match these filters"
          description="Clear one or more filters to see Findings for this Review Run."
        />
      ) : (
        <ul className="findings-list">
          {visibleFindings.map((finding) => (
            <li key={finding.id}>
              <button
                type="button"
                className={`finding finding-button severity-${finding.severity.toLowerCase()}`}
                onClick={() => onSelectFinding?.(finding.id)}
              >
                <div className="finding-header">
                  <span className="finding-source">{finding.source}</span>
                  <span className="finding-severity">{finding.severity}</span>
                  <span className="finding-disposition">
                    {finding.disposition}
                  </span>
                  <strong>{finding.title}</strong>
                </div>
                <p className="finding-category">{finding.category}</p>
                <p className="finding-endpoint">{finding.endpoint}</p>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
