import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import "assets/vendor/nucleo/css/nucleo.css";
import "assets/vendor/font-awesome/css/font-awesome.min.css";
import "assets/scss/argon-design-system-react.scss?v1.1.0";

import Index from "views/Index.js";
import Landing from "views/examples/Landing.js";
import Login from "views/examples/Login.js";
import ForgotPassword from "views/examples/ForgotPassword.js";
import VerifyEmail from "views/examples/VerifyEmail.js";
import ResetPassword from "views/examples/ResetPassword.js";
import Profile from "views/examples/Profile.js";
import Register from "views/examples/Register.js";

const root = ReactDOM.createRoot(document.getElementById("root"));

root.render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<Index />} />
      <Route path="/landing-page" element={<Landing />} />
      <Route path="/login-page" element={<Login />} />
      <Route path="/forgot-password-page" element={<ForgotPassword />} />
      <Route path="/reset-password/:uid/:token" element={<ResetPassword />} />
      <Route path="/profile-page" element={<Profile />} />
      <Route path="/profile-page/:username" element={<Profile />} />
      <Route path="/register-page" element={<Register />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  </BrowserRouter>
);
