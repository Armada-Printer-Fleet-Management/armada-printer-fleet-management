import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from './card';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from './collapsible';

/** A legal document as the about box lists it. */
export interface AboutLegalDocument {
  /** What the document is, such as Licence or Privacy Policy. */
  label: string;
  title: string;
  /** The day this version took effect, YYYY-MM-DD. */
  effectiveDate: string;
  /** The document's text, or undefined when this build does not ship that version. */
  text: string | undefined;
}

export interface AboutBoxProps {
  organization: {
    title: string;
    description: string;
    repositoryUrl: string;
  };
  legalDocuments: AboutLegalDocument[];
  version?: {
    major: number;
    minor: number;
    maintenance: number;
    postfix?: string;
  };
}

const row = 'grid grid-cols-[8rem_minmax(0,1fr)] gap-x-4';

export function AboutBox({
  organization,
  legalDocuments,
  version,
}: AboutBoxProps) {
  const versionText = version
    ? `${version.major}.${version.minor}.${version.maintenance}${version.postfix ? `-${version.postfix}` : ''}`
    : 'unavailable';

  return (
    <Card className="w-full max-w-xl">
      <CardHeader>
        <CardTitle>{organization.title}</CardTitle>
        <CardDescription className="text-foreground/70">
          {organization.description}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <dl className="grid gap-4 text-sm">
          <div className={row}>
            <dt className="font-medium text-foreground/70">Version</dt>
            <dd>{versionText}</dd>
          </div>
          {legalDocuments.map((document) => (
            <div key={`${document.label}-${document.title}`} className={row}>
              <dt className="font-medium text-foreground/70">
                {document.label}
              </dt>
              <dd className="min-w-0">
                <Collapsible>
                  <CollapsibleTrigger>
                    <span className="flex-1">
                      {document.title}, effective {document.effectiveDate}
                    </span>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    {document.text === undefined ? (
                      <p>
                        This copy does not include the text of this version.
                      </p>
                    ) : (
                      <pre
                        tabIndex={0}
                        aria-label={`${document.title} text`}
                        className="max-h-80 overflow-y-auto whitespace-pre-wrap rounded-lg border bg-background p-4 font-mono text-xs focus-visible:outline-2 focus-visible:outline-primary"
                      >
                        {document.text}
                      </pre>
                    )}
                  </CollapsibleContent>
                </Collapsible>
              </dd>
            </div>
          ))}
          <div className={row}>
            <dt className="font-medium text-foreground/70">Source</dt>
            <dd className="min-w-0">
              <a
                className="break-all text-primary underline-offset-4 hover:underline"
                href={organization.repositoryUrl}
              >
                {organization.repositoryUrl}
              </a>
            </dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}
