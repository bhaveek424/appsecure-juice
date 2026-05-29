type LoadingProps = {
  label: string;
};

export function LoadingState({ label }: LoadingProps) {
  return (
    <p className="workbench-state workbench-loading" role="status">
      {label}
    </p>
  );
}

type EmptyProps = {
  title: string;
  description: string;
};

export function EmptyState({ title, description }: EmptyProps) {
  return (
    <div className="workbench-state workbench-empty">
      <h4>{title}</h4>
      <p className="muted">{description}</p>
    </div>
  );
}

type ErrorProps = {
  title: string;
  message: string;
};

export function ErrorBanner({ title, message }: ErrorProps) {
  return (
    <div className="workbench-state workbench-error status-bad" role="alert">
      <strong>{title}</strong>
      <p>{message}</p>
    </div>
  );
}
