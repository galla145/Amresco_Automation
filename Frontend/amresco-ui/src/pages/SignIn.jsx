import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "../services/supabaseClient";

import logo from "../assets/logo.png";
import hero from "../assets/hero.png";

import "./signin.css";

export default function SignIn() {

  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async (e) => {

    e.preventDefault();

    const { data, error } = await supabase.auth.signInWithPassword({
      email: email,
      password: password
    });

    if (error) {
      alert(error.message);
      return;
    }

    /* IMPORTANT: store login state */
    localStorage.setItem("user", JSON.stringify(data.user));

    /* redirect after login */
    navigate("/");

  };

  return (

    <div className="container">

      {/* NAVBAR */}

      <header className="navbar">

        <div className="nav-left">
          <img src={logo} alt="logo" />
        </div>

        <nav className="nav-links">

          <a onClick={() => navigate("/")}>
            Home
          </a>

          <a onClick={() => navigate("/dashboard")}>
            Dashboard
          </a>

          <a>Features</a>

          <a>Reports</a>

          <a>Help</a>

          <button className="signin active">
            Sign In
          </button>

        </nav>

      </header>


      {/* SIGNIN SECTION */}

      <section className="signin-section">

        {/* LEFT SIDE */}

        <div className="signin-left">

          <h1>
            Welcome Back to <br />
            <span>AMRESCO Automation</span>
          </h1>

          <p>
            Sign in to continue your AI-powered Excel
            analysis and automation workflow.
          </p>


          <div className="signin-card">

            <h3>Sign In</h3>

            <form onSubmit={handleLogin}>

              <input
                type="email"
                placeholder="Email Address"
                value={email}
                onChange={(e)=>setEmail(e.target.value)}
                required
              />

              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e)=>setPassword(e.target.value)}
                required
              />

              <button
                type="submit"
                className="login-btn"
              >
                Login
              </button>

            </form>
            <p className="signup-link">
               Don't have an account?{" "}
               <span onClick={() => navigate("/signup")}>
                  Create New User
                </span>
            </p>
            <p className="forgot-link">
               <span onClick={() => navigate("/forgot-password")}>
                  Forgot Password?
               </span>
            </p>
          </div>

        </div>


        {/* RIGHT SIDE */}

        <div className="signin-right">

          <img
            src={hero}
            className="hero-img"
            alt="hero"
          />

        </div>

      </section>

    </div>

  );

}