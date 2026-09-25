import { read } from "@organization-info/organization-info";
import { AboutBox } from "@ui-kit/about-box";
import React from "react";
import { OrganizationInfoSchema } from "./gen/common/v1/organization_info_pb";
import { version } from "./lib/version";

const App: React.FC = () => {
  return (
    <div className="app">
      <header>
        <AboutBox organization={read(OrganizationInfoSchema)} version={version()} />
      </header>
      <main>
        <p>Welcome to the web application. Replace this with real pages and routes.</p>
      </main>
    </div>
  );
};

export default App;