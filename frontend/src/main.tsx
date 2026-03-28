import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import App from "./App";
import Landing from "./pages/Landing";
import IntakeForm from "./pages/IntakeForm";
import AnalysisLoading from "./pages/AnalysisLoading";
import Results from "./pages/Results";
import CaseStudy from "./pages/CaseStudy";
import "./App.css";

const router = createBrowserRouter([
  {
    element: <App />,
    children: [
      { path: "/", element: <Landing /> },
      { path: "/intake", element: <IntakeForm /> },
      { path: "/loading", element: <AnalysisLoading /> },
      { path: "/results", element: <Results /> },
      { path: "/case-study", element: <CaseStudy /> },
    ],
  },
]);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
);
