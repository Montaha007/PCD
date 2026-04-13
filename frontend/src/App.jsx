import Landing from "./pages/Landing";
import Register from "./pages/accounts/Register";
import Login from "./pages/accounts/Login";
import Profile from "./pages/profile/Profile";
import AppSection from "./pages/AppSection";
import SleepLog from "./pages/sleeplog/SleepLog";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { UserDataProvider } from "./context/UserDataContext";
import { Toaster } from "sonner";

function App() {
  return (
    <UserDataProvider>
    <Toaster
      theme="dark"
      position="bottom-right"
      toastOptions={{
        style: {
          background: 'linear-gradient(160deg, rgba(8,14,38,0.96), rgba(6,12,28,0.92))',
          border: '1px solid rgba(100,160,255,0.2)',
          color: '#e8eef8',
          backdropFilter: 'blur(20px)',
        },
      }}
    />
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route
          path="/dashboard"
          element={
            <AppSection
              title="Dashboard"
              description="Your sleep readiness snapshot, trends, and action highlights will live here."
            />
          }
        />
        <Route path="/sleep-log" element={<SleepLog />} />
        <Route
          path="/lifestyle"
          element={
            <AppSection
              title="Lifestyle"
              description="Capture daily habits like caffeine, screens, meals, and activity."
            />
          }
        />
        <Route
          path="/journal"
          element={
            <AppSection
              title="Journal"
              description="Store your mood, thoughts, and emotional patterns alongside sleep data."
            />
          }
        />
        <Route
          path="/routine-optimizer"
          element={
            <AppSection
              title="Routine Optimizer"
              description="Build and refine a bedtime routine based on your personal signals."
            />
          }
        />
        <Route
          path="/audio-therapy"
          element={
            <AppSection
              title="Audio Therapy"
              description="Curate relaxing sound sessions and monitor what helps you fall asleep faster."
            />
          }
        />
        <Route
          path="/weekly-report"
          element={
            <AppSection
              title="Weekly Report"
              description="Review your week with summarized trends, wins, and recovery targets."
            />
          }
        />
        <Route path="/profile" element={<Profile />} />
      </Routes>
    </Router>
    </UserDataProvider>
  );
}

export default App;
