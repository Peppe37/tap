import { Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import { AppLayout } from "@/components/AppLayout";
import { Spinner } from "@/components/Feedback";
import { LoginPage } from "@/features/auth/LoginPage";
import { ConnectionsPage } from "@/features/settings/ConnectionsPage";
import { FirstRunSetup } from "@/features/setup/FirstRunSetup";
import { AddTrackerWizard } from "@/features/trackers/AddTrackerWizard";
import { EditTrackerPage } from "@/features/trackers/EditTrackerPage";
import { TrackerDetail } from "@/features/trackers/TrackerDetail";
import { TrackerList } from "@/features/trackers/TrackerList";

export function App() {
  const { user, isLoading, needsSetup } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner label="Avvio di tap..." />
      </div>
    );
  }

  if (needsSetup) {
    return <FirstRunSetup />;
  }

  if (!user) {
    return <LoginPage />;
  }

  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<TrackerList />} />
        <Route path="/packages/new" element={<AddTrackerWizard />} />
        <Route path="/packages/:id" element={<TrackerDetail />} />
        <Route path="/packages/:id/edit" element={<EditTrackerPage />} />
        <Route path="/settings/connections" element={<ConnectionsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppLayout>
  );
}
