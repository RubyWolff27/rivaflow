import { lazy, Suspense, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ToastProvider } from './contexts/ToastContext';
import PrivateRoute from './components/PrivateRoute';
import AdminRoute from './components/AdminRoute';
import Layout from './components/Layout';
import PageSkeleton from './components/PageSkeleton';
import ErrorBoundary from './components/ErrorBoundary';
import { logger } from './utils/logger';

// Lazy load all route components for code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'));
const LogSession = lazy(() => import('./pages/LogSession'));
const Sessions = lazy(() => import('./pages/Sessions'));
const Feed = lazy(() => import('./pages/Feed'));
const SessionDetail = lazy(() => import('./pages/SessionDetail'));
const Reports = lazy(() => import('./pages/Reports'));
const Readiness = lazy(() => import('./pages/Readiness'));
const ReadinessDetail = lazy(() => import('./pages/ReadinessDetail'));
const EditReadiness = lazy(() => import('./pages/EditReadiness'));
const RestDetail = lazy(() => import('./pages/RestDetail'));
const EditRest = lazy(() => import('./pages/EditRest'));
const Techniques = lazy(() => import('./pages/Techniques'));
const Videos = lazy(() => import('./pages/Videos'));
const Profile = lazy(() => import('./pages/Profile'));
const Glossary = lazy(() => import('./pages/Glossary'));
const MovementDetail = lazy(() => import('./pages/MovementDetail'));
const Friends = lazy(() => import('./pages/Friends'));
const FindFriends = lazy(() => import('./pages/FindFriends'));
const EditSession = lazy(() => import('./pages/EditSession'));
const Chat = lazy(() => import('./pages/Chat'));
const UserProfile = lazy(() => import('./pages/UserProfile'));
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));
const AdminGyms = lazy(() => import('./pages/AdminGyms'));
const AdminUsers = lazy(() => import('./pages/AdminUsers'));
const AdminContent = lazy(() => import('./pages/AdminContent'));
const AdminTechniques = lazy(() => import('./pages/AdminTechniques'));
const Grapple = lazy(() => import('./pages/Grapple'));
const AdminGrapple = lazy(() => import('./pages/AdminGrapple'));
const AdminFeedback = lazy(() => import('./pages/AdminFeedback'));
const AdminWaitlist = lazy(() => import('./pages/AdminWaitlist'));
const AdminEmail = lazy(() => import('./pages/AdminEmail'));
const Waitlist = lazy(() => import('./pages/Waitlist'));
const Events = lazy(() => import('./pages/Events'));
const FightDynamics = lazy(() => import('./pages/FightDynamics'));
const ContactUs = lazy(() => import('./pages/ContactUs'));
const FAQ = lazy(() => import('./pages/FAQ'));
const Terms = lazy(() => import('./pages/Terms'));
const Privacy = lazy(() => import('./pages/Privacy'));
const Groups = lazy(() => import('./pages/Groups'));
const MyGame = lazy(() => import('./pages/MyGame'));
const MonthlyGoals = lazy(() => import('./pages/MonthlyGoals'));
const CoachSettings = lazy(() => import('./pages/CoachSettings'));
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'));
const ResetPassword = lazy(() => import('./pages/ResetPassword'));
const NotFound = lazy(() => import('./pages/NotFound'));

function App() {
  useEffect(() => {
    const handler = (event: PromiseRejectionEvent) => {
      logger.error('Unhandled promise rejection:', event.reason);
    };
    window.addEventListener('unhandledrejection', handler);
    return () => window.removeEventListener('unhandledrejection', handler);
  }, []);

  return (
    <ErrorBoundary>
      <Router>
        <AuthProvider>
          <ToastProvider>
            <Suspense fallback={<PageSkeleton />}>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/waitlist" element={<Waitlist />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/reset-password" element={<ResetPassword />} />
              <Route
                path="/*"
                element={
                  <PrivateRoute>
                    <Layout>
                      <Suspense fallback={<PageSkeleton />}>
                        <Routes>
                          <Route path="/" element={<Dashboard />} />
                          <Route path="/log" element={<LogSession />} />
                          <Route path="/sessions" element={<Sessions />} />
                          <Route path="/session/:id" element={<SessionDetail />} />
                          <Route path="/session/edit/:id" element={<EditSession />} />
                          <Route path="/feed" element={<Feed />} />
                          <Route path="/chat" element={<Chat />} />
                          <Route path="/reports" element={<Reports />} />
                          <Route path="/progress" element={<Reports />} />
                          <Route path="/readiness" element={<Readiness />} />
                          <Route path="/readiness/:date" element={<ReadinessDetail />} />
                          <Route path="/readiness/edit/:date" element={<EditReadiness />} />
                          <Route path="/rest/:date" element={<RestDetail />} />
                          <Route path="/rest/edit/:date" element={<EditRest />} />
                          <Route path="/techniques" element={<Techniques />} />
                          <Route path="/videos" element={<Videos />} />
                          <Route path="/glossary" element={<Glossary />} />
                          <Route path="/glossary/:id" element={<MovementDetail />} />
                          <Route path="/friends" element={<Friends />} />
                          <Route path="/find-friends" element={<FindFriends />} />
                          <Route path="/profile" element={<Profile />} />
                          <Route path="/users/:userId" element={<UserProfile />} />
                          <Route path="/grapple" element={<Grapple />} />
                          <Route path="/coach-settings" element={<CoachSettings />} />
                          <Route path="/my-game" element={<MyGame />} />
                          <Route path="/goals" element={<MonthlyGoals />} />
                          <Route path="/admin" element={<AdminRoute><AdminDashboard /></AdminRoute>} />
                          <Route path="/admin/users" element={<AdminRoute><AdminUsers /></AdminRoute>} />
                          <Route path="/admin/gyms" element={<AdminRoute><AdminGyms /></AdminRoute>} />
                          <Route path="/admin/content" element={<AdminRoute><AdminContent /></AdminRoute>} />
                          <Route path="/admin/techniques" element={<AdminRoute><AdminTechniques /></AdminRoute>} />
                          <Route path="/admin/grapple" element={<AdminRoute><AdminGrapple /></AdminRoute>} />
                          <Route path="/admin/feedback" element={<AdminRoute><AdminFeedback /></AdminRoute>} />
                          <Route path="/admin/waitlist" element={<AdminRoute><AdminWaitlist /></AdminRoute>} />
                          <Route path="/admin/email" element={<AdminRoute><AdminEmail /></AdminRoute>} />
                          <Route path="/groups" element={<Groups />} />
                          <Route path="/events" element={<Events />} />
                          <Route path="/fight-dynamics" element={<FightDynamics />} />
                          <Route path="/contact" element={<ContactUs />} />
                          <Route path="/faq" element={<FAQ />} />
                          <Route path="/terms" element={<Terms />} />
                          <Route path="/privacy" element={<Privacy />} />
                          <Route path="*" element={<NotFound />} />
                        </Routes>
                      </Suspense>
                    </Layout>
                  </PrivateRoute>
                }
              />
            </Routes>
          </Suspense>
        </ToastProvider>
      </AuthProvider>
    </Router>
    </ErrorBoundary>
  );
}

export default App;
