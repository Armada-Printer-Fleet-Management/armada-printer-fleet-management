import {
  AboutBox,
  type AboutLegalDocument,
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
  HomeIcon,
  LegalAgreementDialog,
  OrganizationLogo,
  PrinterIcon,
  SegmentedControl,
  SettingsIcon,
  SignInControls,
  SignInDialog,
  ThemeSwitcher,
  Tooltip,
} from '@armada/ui-kit';
import { type ReactNode, useState } from 'react';

// Long enough to scroll, with an unbroken run that must wrap rather than overflow its box.
const sampleText = [
  'Example licence text for the kitchen sink.',
  'http://localhost/a-very-long-address-with-no-spaces-that-must-wrap-inside-its-box/'.repeat(
    3,
  ),
  ...Array.from({ length: 30 }, (_, line) => `Line ${line + 1} of the text.`),
].join('\n');

const legalDocuments: AboutLegalDocument[] = [
  {
    label: 'Licence',
    title: 'Example Licence',
    effectiveDate: '2026-01-01',
    text: sampleText,
  },
];

const thirdPartyLicences: AboutLegalDocument[] = [
  {
    label: 'Font licence',
    title: 'Example Font Licence',
    effectiveDate: '2026-01-01',
    text: sampleText,
  },
];

type View = 'list' | 'grid';

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="grid gap-3">
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="flex flex-wrap items-start gap-4">{children}</div>
    </section>
  );
}

/**
 * Every ui-kit component in its common states, on one page, so browser tests can check what is
 * actually drawn. `dialog` opens one modal dialog over the page, since only one can be open.
 */
export function KitchenSink({ dialog }: { dialog: string | null }) {
  const [view, setView] = useState<View>('list');

  return (
    <main className="grid min-h-screen gap-8 bg-background p-6 text-foreground">
      <header className="flex flex-wrap items-center gap-4">
        <OrganizationLogo />
        <h1 className="text-2xl font-semibold">ui-kit kitchen sink</h1>
        <ThemeSwitcher className="ml-auto" />
      </header>

      {/* ThemeSwitcher always names its radio group the same, so the page holds only the one in
          the header; this control shows the icon-only, vertical layout instead. */}
      <Section title="Segmented control">
        <SegmentedControl
          label="View"
          name="view"
          options={[
            { value: 'list', label: 'List', icon: HomeIcon },
            { value: 'grid', label: 'Grid', icon: PrinterIcon },
          ]}
          value={view}
          onValueChange={setView}
        />
        <SegmentedControl
          label="Compact view"
          name="compact-view"
          options={[
            { value: 'list', label: 'List', icon: HomeIcon },
            { value: 'grid', label: 'Grid', icon: PrinterIcon },
          ]}
          value={view}
          onValueChange={setView}
          iconOnly
          orientation="vertical"
        />
      </Section>

      <Section title="Tooltip">
        <Tooltip label="Settings">
          <button
            type="button"
            aria-label="Settings"
            className="rounded-md p-2 text-muted-foreground hover:bg-secondary-hover hover:text-foreground focus-visible:outline-2 focus-visible:outline-ring"
          >
            <SettingsIcon className="size-5" />
          </button>
        </Tooltip>
      </Section>

      <Section title="Cards">
        <Card className="w-80">
          <CardHeader>
            <CardTitle>Card title</CardTitle>
            <CardDescription>A short description of the card.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm">Card content in the body text colour.</p>
          </CardContent>
          <CardFooter>
            <p className="text-sm text-muted-foreground">Footer</p>
          </CardFooter>
        </Card>
        <div className="grid w-80 gap-2">
          <Collapsible>
            <CollapsibleTrigger>Closed section</CollapsibleTrigger>
            <CollapsibleContent>Hidden until opened.</CollapsibleContent>
          </Collapsible>
          <Collapsible open>
            <CollapsibleTrigger>Open section</CollapsibleTrigger>
            <CollapsibleContent>
              <p className="text-sm">Shown while open.</p>
            </CollapsibleContent>
          </Collapsible>
        </div>
      </Section>

      <Section title="Sign in">
        <SignInControls className="w-72" status="idle" onSignIn={() => {}} />
        <SignInControls
          className="w-72"
          status="waiting"
          waitingHint="Finish signing in in the other window."
          onSignIn={() => {}}
          onRestart={() => {}}
        />
        <SignInControls
          className="w-72"
          status="error"
          error="The sign-in server could not be reached."
          onSignIn={() => {}}
        />
      </Section>

      <Section title="About box">
        <AboutBox
          organization={{
            title: 'Example Organization',
            description: 'An example organization for the kitchen sink.',
            repositoryUrl: 'http://localhost/repository',
          }}
          legalDocuments={legalDocuments}
          thirdPartyLicences={thirdPartyLicences}
          version={{ major: 1, minor: 2, maintenance: 3, postfix: 'rc.1' }}
        />
      </Section>

      <SignInDialog
        open={dialog === 'sign-in'}
        description="Sign in to send a print."
        status="idle"
        onSignIn={() => {}}
        onDismiss={() => {}}
      />
      {dialog === 'legal' && (
        <LegalAgreementDialog
          applicationTitle="Example Organization"
          documents={legalDocuments}
          notices={thirdPartyLicences}
          onAcceptAll={() => {}}
        />
      )}
    </main>
  );
}
