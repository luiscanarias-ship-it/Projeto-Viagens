import React, { useEffect, useRef } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { LanguageProvider, useLanguage } from "./contexts/LanguageContext";
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
import InviteOnboarding from "./pages/InviteOnboarding";
import AmbassadorProfile from "./pages/AmbassadorProfile";
import InvitePage from "./pages/InvitePage";
import CookieConsent from "./components/CookieConsent";
import CookiePolicy from "./pages/CookiePolicy";
import Privacy from "./pages/Privacy";
import Terms from "./pages/Terms";
import SupportNewTicket from "./pages/SupportNewTicket";
import SupportTicketDetail from "./pages/SupportTicketDetail";
import TestimonialResult from "./pages/TestimonialResult";
import About from "./pages/About";
import PlanTrip from "./pages/PlanTrip";
import TravelPlanner from "./pages/TravelPlanner";
import PublicPlan from "./pages/PublicPlan";

// Syncs user's preferred language on login
const LanguageSync = () => {
  const { user } = useAuth();
  const { syncFromUser } = useLanguage();
  const synced = useRef(false);

  useEffect(() => {
    if (user?.preferred_language && !synced.current) {
      synced.current = true;
      syncFromUser(user.preferred_language);
    }
    if (!user) synced.current = false;
  }, [user, syncFromUser]);

  return null;
};

// Scroll to top on route change
const ScrollToTop = () => {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
};

// Router wrapper to handle auth callback
const AppRouter = () => {
  const location = useLocation();
  
  // Check URL fragment for session_id (Google Auth callback)
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  // Onboarding pages without header/footer
  if (location.pathname === '/onboarding' || location.pathname === '/onboarding/invite') {
    return (
      <Routes>
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/onboarding/invite" element={<InviteOnboarding />} />
      </Routes>
    );
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
          <Route path="/onboarding/invite" element={<InviteOnboarding />} />
          <Route path="/ambassador/:userId" element={<AmbassadorProfile />} />
          <Route path="/invite/:alias" element={<InvitePage />} />
          <Route path="/politica-cookies" element={<CookiePolicy />} />
          <Route path="/cookies" element={<CookiePolicy />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/privacy-policy" element={<Privacy />} />
          <Route path="/terms" element={<Terms />} />
          <Route path="/support/new" element={<SupportNewTicket />} />
          <Route path="/support/:ticketId" element={<SupportTicketDetail />} />
          <Route path="/testimonial/result" element={<TestimonialResult />} />
          <Route path="/about" element={<About />} />
          <Route path="/plan-trip" element={<PlanTrip />} />
          <Route path="/travel-planner" element={<TravelPlanner />} />
          <Route path="/plano/:slug" element={<PublicPlan />} />
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
            <ScrollToTop />
            <LanguageSync />
            <AppRouter />
            <CookieConsent />
          </BrowserRouter>
          <Toaster position="bottom-center" richColors />
        </LanguageProvider>
      </AuthProvider>
    </div>
  );
}

export default App;
