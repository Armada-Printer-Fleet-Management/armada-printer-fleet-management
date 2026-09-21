import React from "react";

const App: React.FC = () => {
  return (
    <div className="app">
      <header>
        <h1>Armada Printer Fleet</h1>
        <div style={{fontSize: '0.9rem', marginTop: '0.5rem'}}>v{ /* version injected by protobuf store */ } <span id="app-version">Example Version</span></div>
      </header>
      <main>
        <p>Welcome to the web application. Replace this with real pages and routes.</p>
      </main>
    </div>
  );
};

export default App;
