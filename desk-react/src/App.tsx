import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';

// Layouts
import { AgentLayout } from './components/layouts/AgentLayout';
import { CustomerLayout } from './components/layouts/CustomerLayout';

// Agent Pages
import { Dashboard } from './pages/Dashboard';
import { TicketList } from './pages/TicketList';
import { TicketDetail } from './pages/TicketDetail';
import { KnowledgeBase } from './pages/KnowledgeBase';

// Customer Pages
import { CustomerTickets } from './pages/CustomerTickets';
import { CustomerTicketDetail } from './pages/CustomerTicketDetail';

// Loading component
function LoadingScreen() {
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto mb-4" />
        <p className="text-muted-foreground">Loading...</p>
      </div>
    </div>
  );
}

function App() {
  const { user, isLoading, isAuthenticated, fetchUser } = useAuthStore();

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    window.location.href = '/login';
    return null;
  }

  const isAgent = user?.user_type === 'Agent';

  return (
    <BrowserRouter basename="/helpdesk">
      <Routes>
        {isAgent ? (
          <Route element={<AgentLayout />}>
            <Route index element={<Navigate to="/tickets" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="tickets" element={<TicketList />} />
            <Route path="tickets/:id" element={<TicketDetail />} />
            <Route path="kb" element={<KnowledgeBase />} />
          </Route>
        ) : (
          <Route element={<CustomerLayout />}>
            <Route index element={<Navigate to="/my-tickets" replace />} />
            <Route path="my-tickets" element={<CustomerTickets />} />
            <Route path="my-tickets/:id" element={<CustomerTicketDetail />} />
          </Route>
        )}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
