import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { LanguageProvider } from "./contexts/LanguageContext";
import { Toaster } from "./components/ui/sonner";

import Header from "./components/Header";
import Footer from "./components/Footer";
import Home from "./pages/Home";
import Login from "./pages/Login";
import AuthCallback from "./pages/AuthCallback";
import JourneyDetail from "./pages/JourneyDetail";
import Dashboard from "./pages/Dashboard";
import Admin from "./pages/Admin";
import PaymentSuccess from "./pages/PaymentSuccess";
import Onboarding from "./pages/Onboarding";
import AmbassadorProfile from "./pages/AmbassadorProfile";
import InvitePage from "./pages/InvitePage";

// Router wrapper to handle auth callback
const AppRouter = () => {
  const location = useLocation();
  
  // Check URL fragment for session_id (Google Auth callback)
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  // Onboarding page without header/footer
  if (location.pathname === '/onboarding') {
    return <Onboarding />;
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route path="/journey/:id" element={<JourneyDetail />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/payment-success" element={<PaymentSuccess />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route path="/ambassador/:userId" element={<AmbassadorProfile />} />
          <Route path="/invite/:alias" element={<InvitePage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
};

function App() {
  return (
    <div className="App noise-overlay">
      <AuthProvider>
        <LanguageProvider>
          <BrowserRouter>
            <AppRouter />
          </BrowserRouter>
          <Toaster position="bottom-center" richColors />
        </LanguageProvider>
      </AuthProvider>
    </div>
  );
}

export default App;
