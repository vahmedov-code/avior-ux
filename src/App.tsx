import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { HeroSection } from './components/HeroSection';
import { ForSection } from './components/ForSection';
import { CaseSection } from './components/CaseSection';
import { ServicesSection } from './components/ServicesSection';
import { ProcessSection } from './components/ProcessSection';
import { ContactSection } from './components/ContactSection';
import { FooterSection } from './components/FooterSection';

export function App() {
  const [entranceComplete, setEntranceComplete] = useState(false);

  return (
    <div 
      className="bg-black text-white selection:bg-white selection:text-black min-h-screen"
      style={{ fontFamily: '"Space Mono", monospace' }}
    >
      <Navbar entranceComplete={entranceComplete} />
      <main>
        <HeroSection onEntranceComplete={() => setEntranceComplete(true)} />
        <ForSection />
        <CaseSection />
        <ServicesSection />
        <ProcessSection />
        <ContactSection />
      </main>
      <FooterSection />
    </div>
  );
}

export default App;
