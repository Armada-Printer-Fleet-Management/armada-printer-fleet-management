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
  thirdPartyLicences?: AboutLegalDocument[];
  version?: {
    major: number;
    minor: number;
    maintenance: number;
    postfix?: string;
  };
}

const row = 'grid grid-cols-[8rem_minmax(0,1fr)] gap-x-4';

function DocumentText({ document }: { document: AboutLegalDocument }) {
  if (document.text === undefined) {
    return <p>This copy does not include the text of this version.</p>;
  }
  return (
    <pre
      tabIndex={0}
      aria-label={`${document.title} text`}
      className="max-h-80 overflow-y-auto whitespace-pre-wrap break-words rounded-lg border bg-background p-4 font-mono text-xs focus-visible:outline-2 focus-visible:outline-primary"
    >
      {document.text}
    </pre>
  );
}

export function AboutBox({
  organization,
  legalDocuments,
  thirdPartyLicences = [],
  version,
}: AboutBoxProps) {
  const versionText = version
    ? `${version.major}.${version.minor}.${version.maintenance}${version.postfix ? `-${version.postfix}` : ''}`
    : 'unavailable';

  return (
    <Card className="w-full max-w-xl">
      <CardHeader>
        <CardTitle>{organization.title}</CardTitle>
        <CardDescription className="text-muted-foreground">
          {organization.description}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <dl className="grid gap-4 text-sm">
          <div className={row}>
            <dt className="font-medium text-muted-foreground">Version</dt>
            <dd>{versionText}</dd>
          </div>
          {legalDocuments.map((document) => (
            <div key={`${document.label}-${document.title}`} className={row}>
              <dt className="font-medium text-muted-foreground">
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
                    <DocumentText document={document} />
                  </CollapsibleContent>
                </Collapsible>
              </dd>
            </div>
          ))}
          {thirdPartyLicences.length > 0 && (
            <div className={row}>
              <dt className="text-xs font-medium text-muted-foreground">
                Third-party licences
              </dt>
              <dd className="min-w-0">
                <Collapsible>
                  <CollapsibleTrigger className="py-2 text-xs">
                    <span className="flex-1">
                      {thirdPartyLicences.length} included
                    </span>
                  </CollapsibleTrigger>
                  <CollapsibleContent className="grid grid-cols-[minmax(0,1fr)] gap-2 text-xs">
                    {thirdPartyLicences.map((licence) => (
                      <Collapsible key={licence.title}>
                        <CollapsibleTrigger className="py-2 text-xs">
                          <span className="flex-1">{licence.title}</span>
                        </CollapsibleTrigger>
                        <CollapsibleContent>
                          <DocumentText document={licence} />
                        </CollapsibleContent>
                      </Collapsible>
                    ))}
                  </CollapsibleContent>
                </Collapsible>
              </dd>
            </div>
          )}
          <div className={row}>
            <dt className="font-medium text-muted-foreground">Source</dt>
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
