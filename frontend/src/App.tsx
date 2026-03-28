import { Outlet, useLocation } from "react-router-dom";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import "./App.css";

export default function App() {
  const { pathname } = useLocation();
  const hideChrome = pathname === "/loading" || pathname === "/intake";

  return (
    <>
      {!hideChrome && <Navbar />}
      <Outlet />
      {!hideChrome && <Footer />}
    </>
  );
}
