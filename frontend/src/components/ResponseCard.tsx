import React from 'react';

interface ResponseCardProps {
  variant: 'A' | 'B';
  content: string;
  onSelect: () => void;
  disabled?: boolean;
}

export const ResponseCard: React.FC<ResponseCardProps> = ({
  variant,
  content,
  onSelect,
  disabled = false,
}) => {
  const wordCount = content.trim().split(/\s+/).filter(Boolean).length;

  return (
    <div className={`response-card response-card-${variant.toLowerCase()}`}>
      <div className="response-header">
        <div className="response-identity">
          <span className={`variant-tag variant-${variant.toLowerCase()}`}>
            Response {variant}
          </span>
          <span className="telemetry-pill">
            {wordCount} words • {content.length} chars
          </span>
        </div>

        <button
          className={`btn-select btn-select-${variant.toLowerCase()}`}
          onClick={onSelect}
          disabled={disabled}
          title={`Select Response ${variant} as superior (Key: ${variant})`}
          aria-label={`Select Response ${variant} as superior`}
        >
          <span>Response {variant} is Better</span>
          <kbd className="key-hint">{variant}</kbd>
        </button>
      </div>

      <div className="response-body">
        <div className="response-content-formatted">
          {content.split('\n\n').map((paragraph, idx) => {
            const trimmed = paragraph.trim();
            if (trimmed.startsWith('```')) {
              const codeLines = trimmed.replace(/^```[a-z]*\n?/, '').replace(/```$/, '');
              return (
                <pre key={idx} className="code-block">
                  <code>{codeLines}</code>
                </pre>
              );
            }
            if (trimmed.startsWith('### ') || trimmed.startsWith('## ') || trimmed.startsWith('# ')) {
              return (
                <h4 key={idx} className="content-heading">
                  {trimmed.replace(/^#+\s*/, '')}
                </h4>
              );
            }
            return (
              <p key={idx} className="content-paragraph">
                {paragraph}
              </p>
            );
          })}
        </div>
      </div>
    </div>
  );
};
