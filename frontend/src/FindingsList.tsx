import { useMemo, useState } from "react";
import type { Finding, FindingCounts } from "./api";
import { SEVERITY_ORDER } from "./api";

type Props = {
  findings: Finding[];
  findingCounts?: FindingCounts;
  onSelectFinding?: (findingId: string) => void;
};

type SortKey = "severity" | "title" | "endpoint";

export default function FindingsList({
  findings,
  findingCounts,
  onSelectFinding,
}: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("severity");

  const sortedFindings = useMemo(() => {
    const items = [...findings];
    items.sort((left, right) => {
      if (sortKey === "severity") {
        const rank =
          SEVERITY_ORDER[left.severity] - SEVERITY_ORDER[right.severity];
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
  }, [findings, sortKey]);

  if (findings.length === 0) {
    return <p className="muted">No findings yet.</p>;
  }

  return (
    <div className="findings">
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
        <label htmlFor="finding-sort">Sort by</label>
        <select
          id="finding-sort"
          value={sortKey}
          onChange={(event) => setSortKey(event.target.value as SortKey)}
        >
          <option value="severity">Severity</option>
          <option value="title">Title</option>
          <option value="endpoint">Endpoint</option>
        </select>
      </div>

      <ul className="findings-list">
        {sortedFindings.map((finding) => (
          <li key={finding.id}>
            <button
              type="button"
              className={`finding finding-button severity-${finding.severity.toLowerCase()}`}
              onClick={() => onSelectFinding?.(finding.id)}
            >
              <div className="finding-header">
                <span className="finding-source">{finding.source}</span>
                <span className="finding-severity">{finding.severity}</span>
                <span className="finding-disposition">{finding.disposition}</span>
                <strong>{finding.title}</strong>
              </div>
              <p className="finding-category">{finding.category}</p>
              <p className="finding-endpoint">{finding.endpoint}</p>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
