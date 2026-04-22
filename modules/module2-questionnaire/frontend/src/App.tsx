import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import { RoleGuard } from "./components/layout/RoleGuard";
import Home from "./routes/Home";
import Login from "./routes/Login";
import Questionnaire from "./routes/Questionnaire";
import UserResult from "./routes/UserResult";
import CoachAdvice from "./routes/CoachAdvice";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />

        {/* user routes — coach 亦可代填問卷 */}
        <Route element={<RoleGuard require={["user", "coach"]} />}>
          <Route path="/u/questionnaire" element={<Questionnaire />} />
        </Route>
        <Route element={<RoleGuard require="user" />}>
          <Route path="/u/result" element={<UserResult />} />
        </Route>

        {/* coach routes */}
        <Route element={<RoleGuard require="coach" />}>
          <Route path="/coach" element={<CoachAdvice />} />
          <Route path="/coach/advice" element={<CoachAdvice />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
